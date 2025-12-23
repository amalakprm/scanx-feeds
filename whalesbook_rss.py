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
    data = resp.json()
    return data.get("data", [])

def build_article_link(item):
    """
    Whalesbook article URLs look like:
    https://www.whalesbook.com/news/English/<newsType>/<slugified-headline>/<id>
    If newsType is missing, fall back to 'All'.
    """
    headline = item.get("headline", "").strip()
    news_type = item.get("newsType", "All") or "All"
    article_id = item.get("id")

    if not headline or not article_id:
        return SITE_ROOT

    # crude slug; good enough for feed linking
    slug = (
        headline.replace(" ", "-")
        .replace("/", "-")
        .replace("?", "")
        .replace("!", "")
        .replace("’", "")
        .replace("'", "")
    )

    return f"{SITE_ROOT}/news/English/{news_type}/{slug}/{article_id}"

def generate_rss_xml(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Whalesbook Financial News"
    ET.SubElement(channel, "link").text = f"{SITE_ROOT}/news/English/All"
    ET.SubElement(channel, "description").text = (
        "Latest Indian financial market news from Whalesbook"
    )
    ET.SubElement(channel, "pubDate").text = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    for item in items:
        title = item.get("headline", "").strip() or "Untitled"
        description = (item.get("shortDescription") or "").strip()
        link = build_article_link(item)
        pub_raw = item.get("scrappedAt") or ""
        image_url = item.get("imageUrl")

        entry = ET.SubElement(channel, "item")
        ET.SubElement(entry, "title").text = title
        ET.SubElement(entry, "link").text = link
        ET.SubElement(entry, "description").text = description

        if pub_raw:
            # keep original ISO timestamp; most readers handle it
            ET.SubElement(entry, "pubDate").text = pub_raw

        if image_url:
            ET.SubElement(
                entry,
                "enclosure",
                attrib={
                    "url": image_url,
                    "type": "image/jpeg",
                },
            )

    return ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")

def main():
    # fetch latest batch; adjust limit if needed
    news_items = fetch_news(limit=40)
    rss_xml = generate_rss_xml(news_items)

    out_file = "whalesbook-news.xml"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print(f"RSS saved to {out_file}")

if __name__ == "__main__":
    main()
