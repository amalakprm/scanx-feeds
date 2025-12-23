import requests
import os
import json
from datetime import datetime

# ================= CONFIG =================
API_URL = "https://api.capitalmarket.com/api/CmLiveNewsHome/A/20"
OUTPUT_FILE = "capital-market-news.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.capitalmarket.com/"
}

def fetch_cm_news():
    print(f"Fetching Live News from Capital Market...")
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        # Load data
        data = response.json()

        # FIX: Some APIs return a string that needs to be parsed again
        if isinstance(data, str):
            articles = json.loads(data)
        else:
            articles = data

        # Ensure we have a list of dictionaries
        if not isinstance(articles, list):
            print(f"Unexpected format: Received {type(articles)}. Expected a list.")
            return

        items_xml = ""
        for art in articles:
            # Another safety check: ensure the item is a dictionary
            if not isinstance(art, dict):
                continue

            # Field Mapping
            title = art.get('Headline', 'Market Update')
            news_id = art.get('NewsId', '0')
            summary = art.get('ShortNews', '')
            category = art.get('CategoryName', 'Market News')
            
            # Web link pattern
            link = f"https://www.capitalmarket.com/News/Live-News/{news_id}"
            
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
    <link>https://www.capitalmarket.com/news/live-news</link>
    <description>Live corporate and market updates from Capital Market India.</description>
    <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    {items_xml}
  </channel>
</rss>"""

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_full)
        print(f"Successfully saved {len(articles)} articles to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error fetching CM news: {e}")

if __name__ == "__main__":
    fetch_cm_news()
