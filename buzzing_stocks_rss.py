import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import hashlib
import sys

URL = "https://www.moneycontrol.com/news/tags/buzzing-stocks.html"
OUT_FILE = "buzzing_stocks.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,*/*;q=0.8"
    ),
    "Accept-Language": "en-IN,en-US;q=0.9,en;q=0.8",
    "Referer": "https://www.moneycontrol.com/",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

session = requests.Session()
session.headers.update(HEADERS)

def fetch_articles():
    r = session.get(URL, timeout=30)

    if r.status_code == 403:
        print("❌ 403 Forbidden – Moneycontrol blocked this IP")
        print("👉 This WILL happen on GitHub Actions sometimes")
        print("👉 Run locally OR use a proxy / self-hosted runner")
        sys.exit(0)

    r.raise_for_status()

    soup = BeautifulSoup(r.text, "html.parser")
    articles = []

    for a in soup.select("a[href*='/news/']"):
        title = a.get_text(strip=True)
        link = a.get("href")

        if not title or not link:
            continue

        if not link.startswith("http"):
            link = "https://www.moneycontrol.com" + link

        if len(title) < 30:
            continue

        articles.append((title, link))

    seen = set()
    clean = []
    for title, link in articles:
        if link not in seen:
            seen.add(link)
            clean.append((title, link))

    return clean[:25]

def build_rss(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Moneycontrol – Buzzing Stocks"
    ET.SubElement(channel, "link").text = URL
    ET.SubElement(channel, "description").text = (
        "Latest Buzzing Stocks news from Moneycontrol (HTML-scraped)"
    )
    ET.SubElement(channel, "language").text = "en-IN"
    ET.SubElement(channel, "lastBuildDate").text = (
        datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    )

    for title, link in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = hashlib.md5(link.encode()).hexdigest()
        ET.SubElement(item, "pubDate").text = (
            datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
        )

    ET.ElementTree(rss).write(
        OUT_FILE,
        encoding="utf-8",
        xml_declaration=True
    )

def main():
    print("Fetching Buzzing Stocks…")
    items = fetch_articles()

    if not items:
        print("⚠️ No articles found (blocked or page changed)")
        sys.exit(0)

    print(f"Found {len(items)} articles")
    build_rss(items)
    print(f"RSS written to: {OUT_FILE}")

if __name__ == "__main__":
    main()
