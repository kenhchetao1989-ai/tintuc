import json
import os
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

RSS_URL = "https://vnexpress.net/rss/tin-moi-nhat.rss"
OUTPUT_FILE = Path("data/news.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

def fetch_rss():
    response = requests.get(RSS_URL, headers=HEADERS, timeout=30)
    response.raise_for_status()
    return response.content

def parse_rss(xml_data):
    root = ET.fromstring(xml_data)
    items = []

    for item in root.findall(".//item")[:20]:
        title = (item.findtext("title") or "").strip()
        link = (item.findtext("link") or "").strip()
        pub_date = (item.findtext("pubDate") or "").strip()
        description = (item.findtext("description") or "").strip()

        if title:
            items.append({
                "source": "vnexpress",
                "title": title,
                "link": link,
                "pubDate": pub_date,
                "description": description
            })

    return {"items": items}

def main():
    os.makedirs("data", exist_ok=True)
    xml_data = fetch_rss()
    data = parse_rss(xml_data)

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(data['items'])} items to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
