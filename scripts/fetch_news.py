import json
import os
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

FEEDS = [
    {
        "source": "vnexpress",
        "url": "https://vnexpress.net/rss/tin-moi-nhat.rss",
    },
    {
        "source": "dantri",
        "url": "https://dantri.com.vn/rss/home.rss",
    },
]

OUTPUT_FILE = Path("data/news.json")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36"
}

def fetch_feed(url):
    response = requests.get(url, headers=HEADERS, timeout=30)
    print(f"URL: {url}")
    print(f"STATUS: {response.status_code}")
    print(response.text[:300])
    response.raise_for_status()
    return response.content

def parse_rss(xml_data, source_name):
    root = ET.fromstring(xml_data)
    items = []

    for item in root.findall(".//item")[:20]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()

        if title:
            items.append({
                "source": source_name,
                "title": title,
                "link": link,
                "pubDate": pub_date,
                "description": description
            })

    return items

def main():
    os.makedirs("data", exist_ok=True)

    all_items = []
    errors = []

    for feed in FEEDS:
        try:
            xml_data = fetch_feed(feed["url"])
            items = parse_rss(xml_data, feed["source"])
            all_items.extend(items)
            print(f"Loaded {len(items)} items from {feed['source']}")
        except Exception as exc:
            errors.append({
                "source": feed["source"],
                "error": str(exc)
            })
            print(f"FAILED {feed['source']}: {exc}")

    payload = {
        "items": all_items[:50],
        "errors": errors
    }

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(all_items)} items to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
