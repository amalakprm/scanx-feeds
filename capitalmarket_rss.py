import requests
import os
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

def create_slug(text):
    """Creates a URL-friendly slug from the headline."""
    if not text: return "news"
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text).strip('-')
    return text

def fetch_cm_news():
    print(f"Connecting to Capital Market API...")
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Check if response is raw string or JSON object
        try:
            data = response.json()
        except:
            data = json.loads(response.text)

        articles = []
        # DRILL DOWN LOGIC: Handle cases where data is a dict or a list
        if isinstance(data, list):
            articles = data
        elif isinstance(data, dict):
            # Capital Market API often nests under these keys
            for key in ['data', 'Result', 'Table', 'CmLiveNewsHome']:
                if isinstance(data.get(key), list):
                    articles = data[key]
                    break
            # Fallback: if no key works, find the first list in the dict
            if not articles:
                for val in data.values():
                    if isinstance(val, list):
                        articles = val
                        break

        if not articles:
            print("No articles found in JSON structure.")
            return

        items_xml = ""
        for art in articles:
            if not isinstance(art, dict): continue

            # Map fields (Handles both PascalCase and camelCase)
            title = art.get('Headline') or art.get('headline') or 'Market Update'
            news_id = art.get('NewsId') or art.get('news_id') or '0'
            summary = art.get('ShortNews') or art.get('short_news') or ''
            category = art.get('CategoryName') or 'Market News'
            
            # Create URL: /markets/news/live-news/slug/newsId
            slug = create_slug(title)
            link = f"{BASE_WEB_URL}/{slug}/{news_id}"
            
            description = f"""
            <strong>Category:</strong> {category}<br/>
            <p>{summary}</p>
            """

            items_xml += f"""
    <item>
      <title><![CDATA[{title}]]></title>
      <link>{link}</link>
      <guid isPermaLink="false">cm-{news_id}</guid>
      <pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
      <description><![CDATA[{description}]]></description>
    </item>"""

        rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Capital Market - Live News</title>
    <link>https://www.capitalmarket.com/markets/news/live-news</link>
    <description>Official Live market updates aggregator.</description>
    <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    {items_xml}
  </channel>
</rss>"""

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_full)
        print(f"Successfully saved {len(articles)} articles to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_cm_news()
