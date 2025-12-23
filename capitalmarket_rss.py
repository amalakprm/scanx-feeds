import requests
import os
import json
import re
from datetime import datetime
from urllib.parse import quote

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
    if not text: 
        return "news"
    text = text.lower().strip()
    # Remove special characters but keep spaces for now
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    # Replace multiple spaces with single hyphen
    text = re.sub(r'\s+', '-', text)
    # Strip leading/trailing hyphens
    text = text.strip('-')
    return text if text else "news"

def fetch_cm_news():
    print(f"Connecting to Capital Market API...")
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        
        data = response.json()
        if not data.get("success"):
            print("API returned unsuccessful response")
            return
            
        articles = data.get("data", [])
        if not articles:
            print("No articles found in API response")
            return

        print(f"Found {len(articles)} articles")

        items_xml = ""
        for art in articles:
            if not isinstance(art, dict): 
                continue

            # Correct field mappings based on actual API response
            title = art.get('Heading', 'Market Update')
            news_id = art.get('SNO', '0')
            caption = art.get('Caption', '') or ''
            section = art.get('sectionname', 'Market News')
            subsection = art.get('subsectionname', '')
            img_url = art.get('IllustrationImage', '')
            
            # Create proper URL slug + ID format
            slug = create_slug(title)
            link = f"{BASE_WEB_URL}/{slug}/{news_id}"
            
            # Build description with available data
            category_info = f"{section}"
            if subsection:
                category_info += f" - {subsection}"
                
            description_parts = []
            if category_info != "Market News":
                description_parts.append(f"<strong>Category:</strong> {category_info}")
            if caption:
                description_parts.append(f"<p>{caption}</p>")
            if img_url:
                description_parts.append(f'<img src="{img_url}" alt="News Image" style="max-width:100%; height:auto;" />')

            description = "<br/>".join(description_parts)

            pub_date_str = f"{art.get('Date', '23 Dec 2025')} {art.get('Time', '18:00')}"
            try:
                # Parse the date properly for RSS
                pub_date = datetime.strptime(pub_date_str, "%d %b %Y %H:%M")
                pub_date_rss = pub_date.strftime("%a, %d %b %Y %H:%M:%S +0000")
            except:
                pub_date_rss = datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")

            items_xml += f"""
    <item>
      <title><![CDATA[{title}]]></title>
      <link>{link}</link>
      <guid isPermaLink="false">cm-{news_id}</guid>
      <pubDate>{pub_date_rss}</pubDate>
      <category>{section}</category>
      <description><![CDATA[{description}]]></description>
    </item>"""

        rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>Capital Market - Live News</title>
    <link>{BASE_WEB_URL}</link>
    <description>Latest market news and updates from Capital Market</description>
    <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    <language>en-us</language>
    <atom:link href="{BASE_WEB_URL}" rel="self" type="application/rss+xml" />
    {items_xml}
  </channel>
</rss>"""

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_full)
        print(f"Successfully generated RSS with {len(articles)} articles -> {OUTPUT_FILE}")

    except requests.exceptions.RequestException as e:
        print(f"Network error: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON parsing error: {e}")
        print(f"Response text: {response.text[:500]}")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    fetch_cm_news()
