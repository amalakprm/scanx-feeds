import requests
import re
from datetime import datetime
from html import escape

# ============= CONFIG =============
API_URL = "https://app1.whalesbook1.shop/published-news-collection/free"
OUTPUT_FILE = "whalesbook-news.xml"

HEADERS = {
    # mimic the request that works in DevTools
    "Accept": "application/json, text/plain, */*",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
}

BASE_WEB_URL = "https://app1.whalesbook1.shop"  # if they expose article pages later


# ============= HELPERS =============
def create_slug(text: str) -> str:
    if not text:
        return "news"
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'\\s+', '-', text)
    text = text.strip('-')
    return text or "news"


# ============= MAIN =============
def fetch_whalesbook_news():
    print("Fetching whalesbook news JSON...")
    r = requests.get(API_URL, headers=HEADERS, timeout=15)
    r.raise_for_status()
    payload = r.json()

    articles = payload.get("data", [])
    if not isinstance(articles, list) or not articles:
        print("No articles found in JSON")
        return

    items_xml = ""

    for art in articles:
        if not isinstance(art, dict):
            continue

        _id = str(art.get("_id", "0"))
        title = art.get("headline") or "News item"
        short_desc = art.get("shortDescription") or ""
        news_type = art.get("newsType") or "News"
        lang = art.get("languageDisplayed") or "English"
        image_url = art.get("imageUrl")  # often null

        # if they ever have a public URL, construct it here; for now use API id
        slug = create_slug(title)
        link = f"{BASE_WEB_URL}/news/{slug}/{_id}"

        # pub date from scrappedAt
        scrapped_at = art.get("scrappedAt")
        try:
            dt = datetime.fromisoformat(scrapped_at.replace("Z", "+00:00"))
            pub_rss = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except Exception:
            pub_rss = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

        # description HTML
        desc_parts = []
        if short_desc:
            desc_parts.append(escape(short_desc))
        desc_parts.append(f"\\n\\n<strong>Type:</strong> {escape(news_type)}")
        desc_parts.append(f"<br/><strong>Language:</strong> {escape(lang)}")
        if image_url:
            desc_parts.append(
                f'<br/><img src="{image_url}" alt="News Image" '
                f'style="max-width:100%; height:auto;" />'
            )

        description = "".join(desc_parts)

        items_xml += f"""
  <item>
    <title><![CDATA[{title}]]></title>
    <link>{link}</link>
    <guid isPermaLink="false">whalesbook-{_id}</guid>
    <pubDate>{pub_rss}</pubDate>
    <category>{escape(news_type)}</category>
    <description><![CDATA[{description}]]></description>
  </item>"""

    rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Whalesbook - Free Published News</title>
    <link>{API_URL}</link>
    <description>Wrapper RSS for app1.whalesbook1.shop free news collection.</description>
    <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    <language>en-us</language>{items_xml}
  </channel>
</rss>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(rss_full)

    print(f"Saved RSS with {len(articles)} items -> {OUTPUT_FILE}")


if __name__ == "__main__":
    fetch_whalesbook_news()
