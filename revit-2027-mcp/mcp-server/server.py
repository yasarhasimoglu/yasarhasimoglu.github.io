#!/usr/bin/env python3
"""
Revit 2027 MCP Sunucusu
=======================

Claude Desktop ile Revit 2027 arasında köprü kuran MCP (Model Context Protocol)
sunucusu. Claude'dan gelen araç çağrılarını, Revit içinde çalışan C# eklentisinin
açtığı TCP sokete (localhost:5577) iletir ve sonucu geri döndürür.

Akış:  Claude Desktop  --stdio-->  bu sunucu  --TCP-->  Revit eklentisi (C#)

Çalıştırma:  python server.py    (genelde Claude Desktop tarafından başlatılır)
"""

import json
import os
import socket
import struct
from typing import Any, Optional

from mcp.server.fastmcp import FastMCP

# Revit eklentisindeki App.Port ile eşleşmeli.
REVIT_HOST = os.environ.get("REVIT_MCP_HOST", "127.0.0.1")
REVIT_PORT = int(os.environ.get("REVIT_MCP_PORT", "5577"))
TIMEOUT_S = float(os.environ.get("REVIT_MCP_TIMEOUT", "300"))

mcp = FastMCP("revit-2027-mcp")


# --------------------------------------------------------------------------- #
# TCP iletişimi (uzunluk-önekli, big-endian int32 + UTF-8 JSON)
# --------------------------------------------------------------------------- #
def _send_command(command: str, params: Optional[dict] = None) -> dict[str, Any]:
    """Revit eklentisine bir komut gönderir ve yanıtı döndürür."""
    payload = json.dumps(
        {"command": command, "params": params or {}}, ensure_ascii=False
    ).encode("utf-8")

    try:
        with socket.create_connection((REVIT_HOST, REVIT_PORT), timeout=TIMEOUT_S) as sock:
            sock.settimeout(TIMEOUT_S)
            sock.sendall(struct.pack(">I", len(payload)) + payload)

            raw_len = _recv_exact(sock, 4)
            (resp_len,) = struct.unpack(">I", raw_len)
            resp = _recv_exact(sock, resp_len).decode("utf-8")
            return json.loads(resp)
    except ConnectionRefusedError:
        return {
            "success": False,
            "error": (
                "Revit'e bağlanılamadı. Revit 2027 açık mı ve 'Revit MCP Plugin' "
                f"eklentisi yüklü mü? ({REVIT_HOST}:{REVIT_PORT})"
            ),
        }
    except socket.timeout:
        return {"success": False, "error": "Revit yanıt vermedi (zaman aşımı)."}
    except Exception as exc:  # noqa: BLE001
        return {"success": False, "error": f"İletişim hatası: {exc}"}


def _recv_exact(sock: socket.socket, count: int) -> bytes:
    buf = bytearray()
    while len(buf) < count:
        chunk = sock.recv(count - len(buf))
        if not chunk:
            raise ConnectionError("Bağlantı beklenmedik şekilde kapandı.")
        buf.extend(chunk)
    return bytes(buf)


def _result(resp: dict) -> str:
    """Eklenti yanıtını okunabilir JSON metnine çevirir."""
    return json.dumps(resp, ensure_ascii=False, indent=2)


# --------------------------------------------------------------------------- #
# MCP Araçları
# --------------------------------------------------------------------------- #
@mcp.tool()
def revit_ping() -> str:
    """Revit eklentisiyle bağlantıyı test eder ve Revit sürümünü döndürür."""
    return _result(_send_command("ping"))


@mcp.tool()
def get_model_info() -> str:
    """Açık Revit modelinin özetini verir: katlar, mahaller (oda+alan),
    aks (grid) sayısı ve görünümler. Diğer işlemlerden önce model durumunu
    görmek için kullanın."""
    return _result(_send_command("get_model_info"))


@mcp.tool()
def set_scale_standard(scale: int = 50, view: Optional[str] = None) -> str:
    """Görünümü 1/50 çizim standardına ayarlar (görünüm ölçeği ve Fine detay).

    Args:
        scale: Görünüm ölçeği paydası (1/50 için 50).
        view: Görünüm adı; boşsa aktif görünüm kullanılır.
    """
    return _result(_send_command("set_scale_standard", {"scale": scale, "view": view}))


@mcp.tool()
def create_grids(
    x_spacings_mm: list[float],
    y_spacings_mm: list[float],
    origin_x_mm: float = 0,
    origin_y_mm: float = 0,
    margin_mm: float = 2000,
) -> str:
    """Aks (grid) sistemi oluşturur. Düşey akslar A, B, C…; yatay akslar 1, 2, 3…
    olarak adlandırılır.

    Args:
        x_spacings_mm: Düşey akslar arası yatay mesafeler, mm. Örn. [4000, 5000, 4000]
            => A, B, C, D aksları (4 düşey aks).
        y_spacings_mm: Yatay akslar arası düşey mesafeler, mm. Örn. [3000, 3500]
            => 1, 2, 3 aksları (3 yatay aks).
        origin_x_mm: A aksının X başlangıcı (mm).
        origin_y_mm: 1 aksının Y başlangıcı (mm).
        margin_mm: Aks çizgilerinin bina dışına taşma payı (mm).
    """
    return _result(
        _send_command(
            "create_grids",
            {
                "x_spacings_mm": x_spacings_mm,
                "y_spacings_mm": y_spacings_mm,
                "origin_x_mm": origin_x_mm,
                "origin_y_mm": origin_y_mm,
                "margin_mm": margin_mm,
            },
        )
    )


@mcp.tool()
def dimension_exterior(
    offset_mm: float = 1500, overall: bool = True, view: Optional[str] = None
) -> str:
    """Aktif plan görünümünde, mevcut aksları referans alarak dış ölçüleri oluşturur:
    bina dışına zincir (ara) ölçü ve toplam (genel) ölçü ekler.

    Args:
        offset_mm: Ölçü çizgisinin binadan uzaklığı (mm).
        overall: True ise ayrıca ilk-son aks arası toplam ölçü eklenir.
        view: Plan görünümü adı; boşsa aktif görünüm.
    """
    return _result(
        _send_command(
            "dimension_exterior",
            {"offset_mm": offset_mm, "overall": overall, "view": view},
        )
    )


@mcp.tool()
def tag_rooms(names: Optional[list[dict]] = None, view: Optional[str] = None) -> str:
    """Aktif plan görünümündeki mahallere (oda) etiket yerleştirir ve isteğe bağlı
    olarak mahal isimlerini ayarlar.

    Args:
        names: Mahal isimlendirme listesi. Her öğe {"number": "101", "name": "OTURMA ODASI"}
            veya {"id": 12345, "name": "MUTFAK"} biçiminde olabilir. Boşsa yalnızca
            etiketleme yapılır.
        view: Plan görünümü adı; boşsa aktif görünüm.
    """
    return _result(_send_command("tag_rooms", {"names": names or [], "view": view}))


@mcp.tool()
def create_schedule(type: str = "rooms", name: Optional[str] = None) -> str:
    """Tablo (schedule) oluşturur.

    Args:
        type: "rooms" (mahal listesi), "doors" (kapı tablosu) veya "windows"
            (pencere tablosu).
        name: Tablo adı; boşsa türüne göre varsayılan ad kullanılır.
    """
    return _result(_send_command("create_schedule", {"type": type, "name": name}))


@mcp.tool()
def calculate_total_area(gross_factor: float = 1.0) -> str:
    """Modeldeki mahal alanlarından toplam (brüt) inşaat alanını ve kat bazında
    dağılımı hesaplar.

    Args:
        gross_factor: Net mahal alanını brüte çevirmek için çarpan (ör. 1.10).
            Mahal alanları zaten brütse 1.0 bırakın.
    """
    return _result(_send_command("calculate_total_area", {"gross_factor": gross_factor}))


@mcp.tool()
def calculate_emsal(
    plot_area_m2: float,
    gross_factor: float = 1.0,
    footprint_level: Optional[str] = None,
    exclude_keywords: Optional[list[str]] = None,
) -> str:
    """Türkiye İmar Yönetmeliği'ne göre emsal (KAKS), TAKS ve toplam inşaat alanını
    hesaplar.

    Args:
        plot_area_m2: Parsel (arsa) alanı, m². Oranlar için zorunludur.
        gross_factor: Net→brüt çarpanı (ör. 1.10).
        footprint_level: TAKS taban alanı için kat adı; boşsa en alt kat kullanılır.
        exclude_keywords: Emsal harici sayılacak mahal adı anahtar kelimeleri
            (ör. ["sığınak", "otopark", "merdiven", "asansör"]). Bu kelimeleri
            içeren mahaller emsal alanından düşülür.
    """
    return _result(
        _send_command(
            "calculate_emsal",
            {
                "plot_area_m2": plot_area_m2,
                "gross_factor": gross_factor,
                "footprint_level": footprint_level,
                "exclude_keywords": exclude_keywords or [],
            },
        )
    )


if __name__ == "__main__":
    mcp.run()
