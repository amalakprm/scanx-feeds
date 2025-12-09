import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from datetime import datetime, timezone
from email.utils import format_datetime


USER_AGENT = "ScanXFeedsBot/1.0 (+https://github.com/amalakprm/scanx-feeds)"
TIMEOUT = 15  # seconds


CATEGORIES = {
    "scanx_stock_news": {
        "title": "ScanX – Stock News",
        "url": "https://scanx.trade/stock-market-news/news-feeds/stock-news",
        "description": "Auto-generated feed for ScanX Stock News",
    },
    "scanx_corporate_actions": {
        "title": "ScanX – Corporate Actions",
        "url": "https://scanx.trade/stock-market-news/corporate-actions",
        "description": "Auto-generated feed for ScanX Corporate Actions",
    },
    "scanx_earnings": {
        "title": "ScanX – Earnings",
        "url": "https://scanx.trade/stock-market-news/earnings",
        "description": "Auto-generated feed for ScanX Earnings",
    },
    "scanx_orders_deals": {
        "title": "ScanX – Orders & Deals",
        "url": "https://scanx.trade/stock-market-news/orders-deals",
        "description": "Auto-generated feed for ScanX Orders & Deals",
    },
    "scanx_global": {
        "title": "ScanX – Global",
        "url": "https://scanx.trade/stock-market-news/global",
        "description": "Auto-generated feed for ScanX Global News",
    },
    "scanx_markets": {
        "title": "ScanX – Markets",
        "url": "https://scanx.trade/stock-market-news/markets",
        "description": "Auto-generated feed for ScanX Markets",
    },
    "scanx_ipo_news": {
        "title": "ScanX – IPO News",
        "url": "https://scanx.trade/stock-market-news/ipo-news",
        "description": "Auto-generated feed for ScanX IPO News",
    },
}


def fetch_html(url: str) -> str:
    resp = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=TIMEOUT,
    )
    resp.raise_for_status()
    resp.encoding = resp.encoding or "utf-8"
    return resp.text


def make_soup(html: str):
    try:
        return BeautifulSoup(html, "lxml")
    except Exception:
        return BeautifulSoup(html, "html.parser")


def extract_items(html: str, base_url: str):
    soup = make_soup(html)
    items = []

    # Each news card is an <a class="article-card" href="..."> ... </a>
    for card in soup.select("a.article-card"):
        href = card.get("href")
        if not href:
            continue

        link = urljoin(base_url, href)

        title_el = (
            card.select_one("span.primaryText.truncate-text.title-hover")
            or card.select_one("span.primaryText")
            or card.select_one("span.title-hover")
            or card
        )
        title = title_el.get_text(" ", strip=True)

        time_el = (
            card.select_one("span.mat-caption-time.forthText.timestamp")
            or card.select_one("span.mat-caption-time")
        )
        rel_time = time_el.get_text(" ", strip=True) if time_el else None

        content = card.select_one("div.content") or card
        description = content.get_text(" ", strip=True)

        items.append(
            {
                "title": title,
                "link": link,
                "description": description,
                "rel_time": rel_time,
            }
        )

    return items


def escape_xml(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def build_rss_xml(feed_id: str, title: str, source_url: str, description: str, items, error: str | None = None):
    now = datetime.now(timezone.utc)
    last_build = format_datetime(now)

    lines = []
    lines.append('<?xml version="1.0" encoding="UTF-8"?>')
    lines.append('<rss version="2.0">')
    lines.append("<channel>")
    lines.append(f"<title>{escape_xml(title)}</title>")
    lines.append(f"<link>{escape_xml(source_url)}</link>")
    lines.append(f"<description>{escape_xml(description)}</description>")
    lines.append(f"<lastBuildDate>{escape_xml(last_build)}</lastBuildDate>")

    if error:
        # Put error info in a single item so you notice if something breaks.
        lines.append("<item>")
        lines.append("<title>Feed error</title>")
        lines.append(f"<description><![CDATA[{escape_xml(error)}]]></description>")
        lines.append("<guid isPermaLink=\"false\">error</guid>")
        lines.append(f"<pubDate>{escape_xml(last_build)}</pubDate>")
        lines.append("</item>")
    else:
        for item in items:
            it_title = item.get("title") or item.get("link") or "Untitled"
            it_link = item.get("link") or ""
            it_desc = item.get("description") or ""
            pub_date = last_build  # simple: build time
            guid = it_link

            lines.append("<item>")
            lines.append(f"<title>{escape_xml(it_title)}</title>")
            if it_link:
                lines.append(f"<link>{escape_xml(it_link)}</link>")
            safe_desc = it_desc.replace("]]>", "]]]]><![CDATA[>")
            lines.append("<description><![CDATA[")
            lines.append(safe_desc)
            lines.append("]]></description>")
            lines.append(f'<guid isPermaLink="true">{escape_xml(guid)}</guid>')
            lines.append(f"<pubDate>{escape_xml(pub_date)}</pubDate>")
            lines.append("</item>")

    lines.append("</channel>")
    lines.append("</rss>")
    return "\n".join(lines)


def main():
    for feed_id, cfg in CATEGORIES.items():
        url = cfg["url"]
        print(f"Fetching {feed_id} from {url}...")
        out_name = f"{feed_id}.xml"
        try:
            html = fetch_html(url)
            items = extract_items(html, url)
            print(f"  -> Extracted {len(items)} items.")
            xml = build_rss_xml(
                feed_id=feed_id,
                title=cfg["title"],
                source_url=url,
                description=cfg["description"],
                items=items,
            )
        except Exception as e:
            msg = f"Error while fetching/parsing: {e!r}"
            print("  !!", msg)
            # Still produce a valid RSS file with error message but no real items
            xml = build_rss_xml(
                feed_id=feed_id,
                title=cfg["title"],
                source_url=url,
                description=cfg["description"],
                items=[],
                error=msg,
            )

        with open(out_name, "w", encoding="utf-8") as f:
            f.write(xml)
        print(f"  -> Wrote {out_name}.")


if __name__ == "__main__":
    main()
