import requests
import os
from datetime import datetime

# ================= CONFIG =================
# A = All news, 20 = Last 20 items
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
        articles = response.json() # Usually returns a list directly

        items_xml = ""
        for art in articles:
            # Field Mapping (Based on Capital Market JSON schema)
            title = art.get('Headline', 'Market Update')
            news_id = art.get('NewsId')
            summary = art.get('ShortNews', '')
            # Try to get the category (e.g., Result, Dividend, Board Meet)
            category = art.get('CategoryName', 'Market News')
            # Capital Market uses a standard date string or timestamp
            raw_date = art.get('NewsDate', '') 
            
            # Construct the web link for the article
            # Capital Market usually follows this pattern:
            link = f"https://www.capitalmarket.com/news/live-news/{news_id}"
            
            description = f"""
            <strong>Category:</strong> {category}<br/>
            <p>{summary}</p>
            <br/>
            <small>News ID: {news_id}</small>
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
