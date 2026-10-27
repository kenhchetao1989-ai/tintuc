# scripts/fetch_news_detail.py
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

INPUT_FILE = Path("data/news.json")
OUTPUT_FILE = Path("data/news_detail.json")

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36",
    "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8"
}

def clean_text(text):
    if not text:
        return ""
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()

def fetch_html(url):
    try:
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"[ERR] {url}: {e}")
        return None

def extract_main_image(soup):
    og = soup.select_one("meta[property='og:image']")
    if og and og.get("content"):
        return og["content"].strip()

    tw = soup.select_one("meta[name='twitter:image']")
    if tw and tw.get("content"):
        return tw["content"].strip()

    for selector in [
        "article img",
        ".article-body img",
        ".detail-content img",
        ".news-content img",
        ".content img",
        "main img"
    ]:
        img = soup.select_one(selector)
        if img:
            src = img.get("src") or img.get("data-src")
            if src:
                return src.strip()
    return ""

def extract_summary(soup):
    meta = soup.select_one("meta[name='description'], meta[property='og:description']")
    if meta and meta.get("content"):
        return clean_text(meta["content"])
    return ""

def extract_content(soup):
    selectors = [
        "article",
        ".article-body",
        ".detail-content",
        ".news-content",
        ".content-detail",
        ".cms-body",
        "main"
    ]

    for selector in selectors:
        article = soup.select_one(selector)
        if article:
            for bad in article.select("script, style, noscript, iframe"):
                bad.decompose()

            parts = []
            for node in article.find_all(["p", "h2", "h3", "figure"]):
                if node.name == "figure":
                    img = node.find("img")
                    if img:
                        src = img.get("src") or img.get("data-src")
                        if src:
                            parts.append(f"<img src='{src.strip()}'>")
                    continue

                text = clean_text(node.get_text(" ", strip=True))
                if text:
                    parts.append(text)

            if parts:
                return "\n\n".join(parts)

    body = soup.body
    if body:
        text = clean_text(body.get_text(" ", strip=True))
        if text:
            return text[:12000]

    return ""

def process_item(item):
    link = item.get("link")
    if not link:
        return None

    html = fetch_html(link)
    if not html:
        return {
            "source": item.get("source"),
            "title": item.get("title"),
            "link": link,
            "pubDate": item.get("pubDate"),
            "status": "failed",
            "image": "",
            "summary": "",
            "content": ""
        }

    soup = BeautifulSoup(html, "html.parser")
    return {
        "source": item.get("source"),
        "title": item.get("title"),
        "link": link,
        "pubDate": item.get("pubDate"),
        "status": "ok",
        "image": extract_main_image(soup),
        "summary": extract_summary(soup),
        "content": extract_content(soup)
    }

def main():
    with INPUT_FILE.open("r", encoding="utf-8") as f:
        data = json.load(f)

    results = []
    items = data.get("items", [])

    for idx, item in enumerate(items[:30], start=1):
        print(f"[{idx}/{len(items)}] {item.get('title')}")
        detail = process_item(item)
        if detail:
            results.append(detail)
        time.sleep(1)

    with OUTPUT_FILE.open("w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"Saved {len(results)} items to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
