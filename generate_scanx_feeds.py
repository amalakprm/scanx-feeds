import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib

USER_AGENT = "ScanXFeedsBot/1.2 (+https://github.com/amalakprm/scanx-feeds)"
TIMEOUT = 15

CATEGORIES = {
    "scanx_stock_news": {
        "title": "ScanX – Stocks",
        "url": "https://scanx.trade/stock-market-news/stocks",
        "description": "ScanX stock market news (Full-Text compatible)",
    },
}

def fetch_html(url: str) -> str:
    r = requests.get(url, headers={"User-Agent": USER_AGENT}, timeout=TIMEOUT)
    r.raise_for_status()
    r.encoding = r.encoding or "utf-8"
    return r.text

def soupify(html: str) -> BeautifulSoup:
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")

def extract_items(html: str, base_url: str):
    soup = soupify(html)
    items = []

    for card in soup.select("a.article-card"):
        href = card.get("href")
        if not href:
            continue

        link = urljoin(base_url, href)

        title = card.get_text(" ", strip=True)
        summary = title  # keep short & clean

        guid = hashlib.sha1(link.encode()).hexdigest()

        items.append({
            "title": title,
            "link": link,
            "summary": summary,
            "guid": guid,
        })

    return items

def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )

def build_rss(feed, items):
    now = format_datetime(datetime.now(timezone.utc))

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append('<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">')
    out.append("<channel>")

    out.append(f"<title>{escape(feed['title'])}</title>")
    out.append(f"<link>{escape(feed['url'])}</link>")
    out.append(f"<description>{escape(feed['description'])}</description>")
    out.append(f"<lastBuildDate>{now}</lastBuildDate>")

    for it in items:
        out.append("<item>")
        out.append(f"<title>{escape(it['title'])}</title>")
        out.append(f"<link>{escape(it['link'])}</link>")
        out.append(f"<guid isPermaLink=\"false\">{it['guid']}</guid>")
        out.append(f"<description>{escape(it['summary'])}</description>")
        out.append(f"<pubDate>{now}</pubDate>")
        out.append("</item>")

    out.append("</channel>")
    out.append("</rss>")
    return "\n".join(out)

def main():
    for feed_id, cfg in CATEGORIES.items():
        print(f"Fetching {feed_id}")
        html = fetch_html(cfg["url"])
        items = extract_items(html, cfg["url"])
        rss = build_rss(cfg, items)

        with open(f"{feed_id}.xml", "w", encoding="utf-8") as f:
            f.write(rss)

        print(f"✔ {feed_id}.xml written ({len(items)} items)")

if __name__ == "__main__":
    main()
