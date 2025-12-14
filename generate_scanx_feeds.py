import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
import sys

TIMEOUT = 20

CATEGORIES = {
    "scanx_stock_news": {
        "title": "ScanX – Stocks",
        "url": "https://scanx.trade/stock-market-news/stocks",
        "description": "ScanX stock market news (Full-Text RSS compatible)",
    },
    "scanx_corporate_actions": {
        "title": "ScanX – Corporate Actions",
        "url": "https://scanx.trade/stock-market-news/corporate-actions",
        "description": "ScanX corporate actions (Full-Text RSS compatible)",
    },
    "scanx_earnings": {
        "title": "ScanX – Earnings",
        "url": "https://scanx.trade/stock-market-news/earnings",
        "description": "ScanX earnings news (Full-Text RSS compatible)",
    },
}

# ---------- HTTP FETCH (403-safe, browser-like) ----------

def fetch_html(url: str) -> str:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/119.0.0.0 Safari/537.36"
        ),
        "Accept": (
            "text/html,application/xhtml+xml,"
            "application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        ),
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://scanx.trade/",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
    }

    r = requests.get(url, headers=headers, timeout=TIMEOUT)

    if r.status_code == 403:
        raise RuntimeError(f"403 Forbidden (bot protection): {url}")

    r.raise_for_status()
    r.encoding = r.encoding or "utf-8"
    return r.text


# ---------- HTML PARSING ----------

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

        if not title or len(title) < 5:
            continue

        guid = hashlib.sha1(link.encode("utf-8")).hexdigest()

        items.append({
            "title": title,
            "link": link,
            "summary": title,
            "guid": guid,
        })

    return items


# ---------- RSS BUILD ----------

def escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_rss(feed_cfg, items):
    now = format_datetime(datetime.now(timezone.utc))

    out = []
    out.append('<?xml version="1.0" encoding="UTF-8"?>')
    out.append(
        '<rss version="2.0" '
        'xmlns:content="http://purl.org/rss/1.0/modules/content/">'
    )
    out.append("<channel>")

    out.append(f"<title>{escape(feed_cfg['title'])}</title>")
    out.append(f"<link>{escape(feed_cfg['url'])}</link>")
    out.append(f"<description>{escape(feed_cfg['description'])}</description>")
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


# ---------- MAIN ----------

def main():
    for feed_id, cfg in CATEGORIES.items():
        print(f"▶ Fetching {feed_id}")

        try:
            html = fetch_html(cfg["url"])
            items = extract_items(html, cfg["url"])

            if not items:
                print("⚠ No items found, skipping update")
                continue

            rss = build_rss(cfg, items)

            with open(f"{feed_id}.xml", "w", encoding="utf-8") as f:
                f.write(rss)

            print(f"✔ {feed_id}.xml written ({len(items)} items)")

        except Exception as e:
            print(f"⚠ {feed_id} failed: {e}", file=sys.stderr)
            print("⚠ Keeping previous feed (fail-soft)")

if __name__ == "__main__":
    main()
