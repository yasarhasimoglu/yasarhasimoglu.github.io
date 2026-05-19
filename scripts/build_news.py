#!/usr/bin/env python3
"""Build news.json from architecture RSS feeds (server-side, no CORS proxy)."""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import xml.etree.ElementTree as ET

FEEDS = [
    ("ArchDaily", "https://www.archdaily.com/rss/", "world"),
    ("Dezeen", "https://www.dezeen.com/feed/", "world"),
    ("Arkitera", "https://www.arkitera.com/feed/", "tr"),
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; hmimar-news-bot/1.0; +https://hmimar.com)",
    "Accept": "application/rss+xml, application/xml, text/xml, */*;q=0.8",
}


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def to_iso(s: str) -> str:
    if not s:
        return ""
    try:
        return parsedate_to_datetime(s).astimezone(timezone.utc).isoformat()
    except Exception:
        try:
            return datetime.fromisoformat(s.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
        except Exception:
            return s


def first_img(html: str) -> str:
    if not html:
        return ""
    m = re.search(r'<img[^>]+src="([^"]+)"', html)
    return m.group(1) if m else ""


def parse(xml_bytes: bytes, source: str, kind: str):
    text = xml_bytes.decode("utf-8", errors="replace")
    # Strip namespaces to simplify XPath-less queries
    text = re.sub(r'\sxmlns(:\w+)?="[^"]+"', "", text)
    try:
        root = ET.fromstring(text)
    except ET.ParseError as e:
        print(f"  parse error: {e}", file=sys.stderr)
        return []
    items = root.findall(".//item")
    if not items:
        items = root.findall(".//entry")
    out = []
    for it in items[:14]:
        def get(tag: str) -> str:
            n = it.find(tag)
            return (n.text or "").strip() if n is not None and n.text else ""

        title = get("title")
        link = get("link")
        if not link:
            ln = it.find("link")
            if ln is not None and ln.get("href"):
                link = ln.get("href")
        date = get("pubDate") or get("updated") or get("published")
        desc = get("description") or get("summary")
        img = ""
        enc = it.find("enclosure")
        if enc is not None and enc.get("url"):
            img = enc.get("url")
        if not img:
            img = first_img(desc)
        if not title or not link:
            continue
        out.append({
            "title": title,
            "link": link,
            "date": to_iso(date),
            "img": img,
            "src": source,
            "kind": kind,
        })
    return out


def main():
    items = []
    for name, url, kind in FEEDS:
        try:
            data = fetch(url)
            got = parse(data, name, kind)
            items.extend(got)
            print(f"OK {name}: +{len(got)} items", file=sys.stderr)
        except Exception as e:
            print(f"FAIL {name}: {e}", file=sys.stderr)
    items.sort(key=lambda x: x["date"] or "", reverse=True)
    out = {
        "generated": datetime.now(timezone.utc).isoformat(),
        "world": [x for x in items if x["kind"] == "world"][:12],
        "tr": [x for x in items if x["kind"] == "tr"][:9],
    }
    with open("news.json", "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"wrote news.json: {len(out['world'])} world + {len(out['tr'])} tr", file=sys.stderr)


if __name__ == "__main__":
    main()
