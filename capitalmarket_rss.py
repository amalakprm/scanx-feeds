import requests
import json
import re
from datetime import datetime

# ================= CONFIG =================
API_URL = "https://api.capitalmarket.com/api/CmLiveNewsHome/A/20"
OUTPUT_FILE = "capital-market-news.xml"
BASE_WEB_URL = "https://www.capitalmarket.com/markets/news/live-news"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.capitalmarket.com/"
}

def create_slug(text: str) -> str:
    """Creates a URL-friendly slug from the headline."""
    if not text:
        return "news"
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\s-]', '', text)     # keep alnum + spaces + hyphen
    text = re.sub(r'\s+', '-', text)             # spaces -> single hyphen
    text = text.strip('-')
    return text or "news"

def clean_summary(text: str) -> str:
    """Collapse whitespace and trim; safe for RSS description first line."""
    if not text:
        return ""
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def fetch_cm_news():
    print("Connecting to Capital Market API...")
    try:
        resp = requests.get(API_URL, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        if not data.get("success"):
            print("API not successful.")
            return

        articles = data.get("data", [])
        if not articles:
            print("No articles found in API response.")
            return

        items_xml = ""

        for art in articles:
            if not isinstance(art, dict):
                continue

            # --- field mapping from API ---
            title   = art.get("Heading") or "Market Update"
            news_id = art.get("SNO") or "0"
            caption = art.get("Caption") or ""
            section = art.get("sectionname") or "Market News"
            subsection = art.get("subsectionname") or ""
            img_url = art.get("IllustrationImage") or ""

            # --- URL ---
            slug = create_slug(title)
            link = f"{BASE_WEB_URL}/{slug}/{news_id}"

            # --- pubDate from API Date + Time ---
            date_str = art.get("Date", "")
            time_str = art.get("Time", "00:00")
            pub_rss = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
            try:
                # Example: "23 Dec 2025" + "17:33"
                dt = datetime.strptime(f"{date_str} {time_str}", "%d %b %Y %H:%M")
                pub_rss = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
            except Exception:
                pass

            # --- plain-text summary for readers/podcast apps ---
            # if you later scrape full article text, plug first paragraph here
            summary_text = clean_summary(caption or title)

            cat_info = section
            if subsection:
                cat_info += f" - {subsection}"

            description_html = summary_text
            description_html += f"\n\n<strong>Category:</strong> {cat_info}<br/>"
            if img_url:
                description_html += (
                    f'<img src="{img_url}" alt="News Image" '
                    f'style="max-width:100%; height:auto;" />'
                )

            items_xml += f"""
    <item>
      <title><![CDATA[{title}]]></title>
      <link>{link}</link>
      <guid isPermaLink="false">cm-{news_id}</guid>
      <pubDate>{pub_rss}</pubDate>
      <category>{section}</category>
      <description><![CDATA[{description_html}]]></description>
    </item>"""

        rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
  <channel>
    <title>Capital Market - Live News</title>
    <link>{BASE_WEB_URL}</link>
    <description>Latest market news and updates from Capital Market</description>
    <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    <language>en-us</language>
    <atom:link href="{BASE_WEB_URL}" rel="self" type="application/rss+xml" />
    {items_xml}
  </channel>
</rss>"""

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_full)

        print(f"Successfully generated RSS with {len(articles)} items -> {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_cm_news()
