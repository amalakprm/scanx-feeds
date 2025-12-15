import requests
from bs4 import BeautifulSoup
from datetime import datetime
import xml.etree.ElementTree as ET
import hashlib
import sys

URL = "https://www.moneycontrol.com/news/tags/buzzing-stocks.html"
ALT_URL = "https://m.moneycontrol.com/news/tags/buzzing-stocks.html"
OUT_FILE = "buzzing_stocks.xml"
TIMEOUT = 20

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.moneycontrol.com/",
    "Connection": "keep-alive",
}

def fetch_articles():
    s = requests.Session()

    # Warm-up: get cookies (often helps with 403 blocks)
    try:
        s.get("https://www.moneycontrol.com/", headers=HEADERS, timeout=TIMEOUT)
    except Exception:
        pass

    for u in (URL, ALT_URL):
        try:
            r = s.get(u, headers=HEADERS, timeout=TIMEOUT)

            # If blocked, try next URL (mobile)
            if r.status_code == 403:
                continue

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

                # Filter junk / navigation
                if len(title) < 30:
                    continue

                articles.append((title, link))

            # Deduplicate by URL
            seen = set()
            clean = []
            for title, link in articles:
                if link not in seen:
                    seen.add(link)
                    clean.append((title, link))

            return clean[:25]  # keep feed clean

        except Exception:
            continue

    # If still blocked or parsing failed, return empty (fail-soft)
    return []

def build_rss(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Moneycontrol – Buzzing Stocks"
    ET.SubElement(channel, "link").text = URL
    ET.SubElement(channel, "description").text = (
        "Latest Buzzing Stocks news from Moneycontrol (auto-generated)"
    )
    ET.SubElement(channel, "language").text = "en-IN"
    ET.SubElement(channel, "lastBuildDate").text = (
        datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    )

    now_gmt = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")

    for title, link in items:
        item = ET.SubElement(channel, "item")
        ET.SubElement(item, "title").text = title
        ET.SubElement(item, "link").text = link
        ET.SubElement(item, "guid").text = hashlib.md5(link.encode()).hexdigest()
        ET.SubElement(item, "pubDate").text = now_gmt

    tree = ET.ElementTree(rss)
    tree.write(OUT_FILE, encoding="utf-8", xml_declaration=True)

def main():
    print("Fetching Buzzing Stocks…")
    items = fetch_articles()
    print(f"Found {len(items)} articles")

    if not items:
        print("Blocked/empty result (likely 403). Keeping previous XML.", file=sys.stderr)
        return

    build_rss(items)
    print(f"RSS written to: {OUT_FILE}")

if __name__ == "__main__":
    main()
