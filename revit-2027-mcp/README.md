# Revit 2027 — Claude Desktop MCP Eklentisi

Claude Desktop'ın doğrudan Revit eklentisi yoktur. Bu proje, aradaki köprüyü
**MCP (Model Context Protocol)** ile kurar: Claude Desktop bir MCP sunucusuyla
konuşur, MCP sunucusu da Revit içinde çalışan bir C# eklentisine komut gönderir.

```
Claude Desktop  ──stdio──►  MCP Sunucusu (Python)  ──TCP 5577──►  Revit Eklentisi (C#)
                                                                   (Revit 2027 içinde çalışır)
```

Bu eklenti ile Claude şunları yapabilir:

| Yetenek | Araç (tool) | Açıklama |
|---|---|---|
| **1/50 standardı** | `set_scale_standard` | Görünümü 1:50 ölçeğe ve Fine detaya ayarlar |
| **Akslar (grid)** | `create_grids` | Düşey (A,B,C…) ve yatay (1,2,3…) aksları üretir |
| **Dış ölçüler** | `dimension_exterior` | Aksları referans alıp zincir + toplam ölçü ekler |
| **Mahal isim + etiket** | `tag_rooms` | Mahal isimlerini yazar ve oda etiketleri yerleştirir |
| **Tablolar** | `create_schedule` | Mahal listesi, kapı ve pencere tabloları oluşturur |
| **Emsal (KAKS) / TAKS** | `calculate_emsal` | İmar Yönetmeliği'ne göre emsal ve TAKS hesaplar |
| **Toplam inşaat alanı** | `calculate_total_area` | Tüm katların brüt alan toplamını verir |
| Model bilgisi | `get_model_info` | Katlar, mahaller, akslar, görünümler özeti |
| Bağlantı testi | `revit_ping` | Revit ile bağlantıyı doğrular |

---

## Klasör yapısı

```
revit-2027-mcp/
├── revit-plugin/        # Revit içinde çalışan C# add-in (.NET 8)
│   ├── App.cs                     # Giriş noktası + soket sunucusunu başlatır
│   ├── SocketServer.cs            # TCP dinleyici (localhost:5577)
│   ├── RevitCommandExecutor.cs    # Komutları Revit ana iş parçacığında çalıştırır
│   ├── CommandDispatcher.cs       # Komut → işleyici yönlendirmesi
│   ├── Util.cs                    # JSON/birim yardımcıları
│   ├── Commands/                  # Her yetenek için bir işleyici
│   ├── RevitMcpPlugin.csproj
│   └── RevitMcpPlugin.addin       # Revit manifest dosyası
└── mcp-server/          # Claude Desktop'ın konuştuğu MCP sunucusu (Python)
    ├── server.py
    ├── requirements.txt
    └── claude_desktop_config.example.json
```

---

## Kurulum

### 1) Revit eklentisini derle ve yükle

Gereksinimler: Windows, Revit 2027, .NET 8 SDK, Visual Studio veya `dotnet` CLI.

```powershell
cd revit-2027-mcp\revit-plugin
dotnet build -c Release
```

- `RevitMcpPlugin.csproj` içindeki `RevitDir`, varsayılan olarak
  `C:\Program Files\Autodesk\Revit 2027\` yolundaki `RevitAPI.dll` ve
  `RevitAPIUI.dll`'i referanslar. Revit farklı bir yerdeyse bu satırı düzenleyin.
- Derleme sonrası **DeployAddin** hedefi, `.addin` dosyasını ve DLL'i otomatik
  olarak şuraya kopyalar:
  `%ProgramData%\Autodesk\Revit\Addins\2027\`
- Revit 2027'yi başlatın. Eklenti yüklendiğinde `localhost:5577` portunda
  dinlemeye başlar ve şeritte (ribbon) **Revit MCP** sekmesi görünür.

### 2) MCP sunucusunu kur

Gereksinim: Python 3.10+

```powershell
cd revit-2027-mcp\mcp-server
pip install -r requirements.txt
```

### 3) Claude Desktop'a tanıt

`%APPDATA%\Claude\claude_desktop_config.json` dosyasını açın ve
`claude_desktop_config.example.json` içeriğini ekleyin (yolları kendi
kurulumunuza göre düzeltin):

```json
{
  "mcpServers": {
    "revit-2027": {
      "command": "python",
      "args": ["C:\\revit-2027-mcp\\mcp-server\\server.py"]
    }
  }
}
```

Claude Desktop'ı yeniden başlatın. Artık araç çubuğunda 🔌 simgesinde
`revit-2027` araçları görünmelidir.

---

## Kullanım (Claude Desktop içinde)

Önce Revit 2027'yi ve bir proje dosyasını açın. Sonra Claude'a doğal dille
sorun. Örnekler:

> **"Revit bağlantısını test et."**
> → `revit_ping`

> **"Aktif planı 1/50 ölçeğine ayarla."**
> → `set_scale_standard(scale=50)`

> **"X yönünde 4000, 5000, 4000; Y yönünde 3000, 3500 aralıklı aks sistemi kur."**
> → `create_grids(x_spacings_mm=[4000,5000,4000], y_spacings_mm=[3000,3500])`

> **"Planda dış ölçüleri at, toplam ölçü de ekle."**
> → `dimension_exterior(offset_mm=1500, overall=True)`

> **"101 numaralı odayı OTURMA ODASI, 102'yi MUTFAK yap ve tüm mahalleri etiketle."**
> → `tag_rooms(names=[{"number":"101","name":"OTURMA ODASI"},{"number":"102","name":"MUTFAK"}])`

> **"Mahal listesi, kapı ve pencere tablolarını oluştur."**
> → `create_schedule(type="rooms")`, `create_schedule(type="doors")`, `create_schedule(type="windows")`

> **"Parsel 500 m². Sığınak, otopark ve merdivenleri emsal harici tutarak emsal ve TAKS hesapla."**
> → `calculate_emsal(plot_area_m2=500, exclude_keywords=["sığınak","otopark","merdiven"])`

> **"Toplam inşaat alanını brüt %10 paylı hesapla."**
> → `calculate_total_area(gross_factor=1.10)`

---

## Emsal / TAKS hesabı nasıl çalışır?

Hesap, modeldeki **Mahaller (Rooms)** üzerinden yapılır:

- **Toplam inşaat alanı** = tüm mahallerin alan toplamı × `gross_factor`
- **Emsal (KAKS)** = (toplam inşaat alanı − emsal harici alanlar) ÷ parsel alanı
- **TAKS** = taban (zemin kat) alanı ÷ parsel alanı
- **Emsal harici alanlar**, adı `exclude_keywords` ile eşleşen mahallerden
  (sığınak, otopark, ortak alan vb.) toplanır ve düşülür.

> **Not:** Mahal alanı Revit ayarına göre genelde net/aks-orta alandır. Resmî
> ruhsat hesabında brüt alan duvar dış yüzüne göre ölçülür; bu nedenle
> `gross_factor` ile düzeltme yapın veya sonucu kontrol edin. Bu araç bir
> ön/kontrol hesabıdır, resmî beyan yerine geçmez.

---

## Sorun giderme

- **"Revit'e bağlanılamadı"**: Revit 2027 açık ve proje yüklü mü? Eklenti
  derlenip `Addins\2027` klasörüne kopyalandı mı? Port 5577 başka bir uygulama
  tarafından kullanılıyorsa `App.Port` ve `REVIT_MCP_PORT`'u birlikte değiştirin.
- **"Görünüm bir plan olmalı"**: Ölçü/etiket komutları aktif bir plan
  görünümü ister. Önce bir kat planını açın.
- **Aks ölçüsü boş çıkıyor**: Önce `create_grids` ile aksları oluşturun;
  `dimension_exterior` mevcut aksları referans alır.
- **Eklenti güvenlik uyarısı**: Revit, imzasız eklentiler için "Always Load"
  onayı isteyebilir; onaylayın.
```
