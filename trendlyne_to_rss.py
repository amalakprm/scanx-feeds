import requests
import re
import os
from datetime import datetime

# ================= CONFIG =================
API_URL = "https://trendlyne.com/api/post/list/?pageNumber=1"
BASE_URL = "https://trendlyne.com"
OUTPUT_FILE = "trendlyne-news.xml"

# Headers are important for Trendlyne to avoid bot detection
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Referer": "https://trendlyne.com/news-by-trendlyne/",
}

def create_slug(text):
    """Creates a URL-friendly slug from the title."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'\s+', '-', text).strip('-')
    return text

def format_date(date_str):
    """Converts ISO date to RSS RFC 822 format."""
    # Trendlyne date: 2025-12-19T11:45:10+00:00
    try:
        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except:
        return date_str

def fetch_and_build_rss():
    print(f"Fetching data from {API_URL}...")
    
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        
        articles = data.get('body', {}).get('main', [])
        
        items_xml = ""
        
        for art in articles:
            title = art.get('title', 'No Title')
            post_id = art.get('postId')
            short_text = art.get('shortText', '')
            image_url = art.get('imageUrl', '')
            pub_date = format_date(art.get('pubDate', ''))
            
            # Generate the Trendlyne URL structure: /posts/ID/slug
            slug = create_slug(title)
            link = f"{BASE_URL}/posts/{post_id}/{slug}/"
            
            # Build Item XML
            items_xml += f"""
    <item>
      <title><![CDATA[{title}]]></title>
      <link>{link}</link>
      <guid isPermaLink="true">{link}</guid>
      <pubDate>{pub_date}</pubDate>
      <description><![CDATA[
        <img src="{image_url}" style="width:100%;" /><br/>
        <p>{short_text}</p>
        <p><strong>Premium:</strong> {'Yes' if art.get('isPremiumPost') else 'No'}</p>
      ]]></description>
    </item>"""

        # Final RSS Assembly
        rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title><![CDATA[Trendlyne Latest Market News]]></title>
    <link>https://trendlyne.com/news-by-trendlyne/</link>
    <description><![CDATA[Latest stock market insights and analyst calls from Trendlyne.]]></description>
    <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    {items_xml}
  </channel>
</rss>"""

        # Write to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_full)
            
        print(f"Successfully wrote RSS to {os.path.abspath(OUTPUT_FILE)}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    fetch_and_build_rss()