import requests
import xml.etree.ElementTree as ET
from datetime import datetime

API_URL = "https://app1.whalesbook1.shop/published-news-collection/free"
SITE_ROOT = "https://www.whalesbook.com"


def fetch_news(date=None, page=1, limit=40, sector="All", language="English"):
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    payload = {
        "date": date,
        "page": page,
        "limit": limit,
        "sector": sector,
        "language": language,
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Origin": SITE_ROOT,
        "Referer": f"{SITE_ROOT}/news/English/All",
    }

    resp = requests.post(API_URL, json=payload, headers=headers, timeout=20)
    resp.raise_for_status()
    return resp.json().get("data", [])


def build_article_link(item):
    """
    CRITICAL:
    Whalesbook URLs are case-sensitive and non-derivable.
    ALWAYS use canonical URL if provided by API.
    """

    # ✅ Always prefer canonical URL from API
    for key in ("newsUrl", "url", "slugUrl"):
        if item.get(key):
            return item[key].strip()

    # ❌ Absolute last-resort fallback (rare)
    article_id = item.get("_id") or item.get("id")
    if not article_id:
        return None

    return f"{SITE_ROOT}/news/{article_id}"


def format_pubdate(iso_ts):
    try:
        dt = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except Exception:
        return None


def generate_rss_xml(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Whalesbook Financial News"
    ET.SubElement(channel, "link").text = f"{SITE_ROOT}/news/English/All"
    ET.SubElement(channel, "description").text = (
        "Latest Indian and global financial market news from Whalesbook"
    )
    ET.SubElement(channel, "pubDate").text = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    for item in items:
        link = build_article_link(item)
        if not link:
            continue

        entry = ET.SubElement(channel, "item")

        ET.SubElement(entry, "title").text = (
            item.get("headline", "Untitled").strip()
        )
        ET.SubElement(entry, "link").text = link
        ET.SubElement(entry, "guid").text = link

        desc = (item.get("shortDescription") or "").strip()
        ET.SubElement(entry, "description").text = desc

        pub = format_pubdate(item.get("scrappedAt", ""))
        if pub:
            ET.SubElement(entry, "pubDate").text = pub

        image_url = item.get("imageUrl")
        if image_url:
            ET.SubElement(
                entry,
                "enclosure",
                attrib={
                    "url": image_url,
                    "type": "image/jpeg",
                },
            )

    return ET.tostring(
        rss, encoding="utf-8", xml_declaration=True
    ).decode("utf-8")


def main():
    items = fetch_news(limit=40)
    rss_xml = generate_rss_xml(items)

    with open("whalesbook-news.xml", "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print("✅ whalesbook-news.xml generated successfully")


if __name__ == "__main__":
    main()
