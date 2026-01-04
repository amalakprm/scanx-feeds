import requests
import base64
import urllib.parse
from datetime import datetime
import json
import re

# ================== CONFIG ==================
# Updated endpoint based on your input
API_URL = "https://api.stockwatch.live/api/keyEvents"
BASE_WEB_URL = "https://www.stockwatch.live/news"
OUTPUT_FILE = "stockwatch-feed.xml"

HEADERS_API = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.stockwatch.live/"
}

# ================= HELPERS ==================
def generate_token(uuid_str):
    """
    Generates the access token required for the news URL.
    Logic: Base64 encode the first 12 characters of the UUID.
    Example: 50a49444-f8b -> NTBhNDk0NDQtZjhi
    """
    if not uuid_str or len(uuid_str) < 12:
        return ""
    subset = uuid_str[:12]
    return base64.b64encode(subset.encode('utf-8')).decode('utf-8')

def format_pubdate(iso_date_str):
    """
    Converts ISO 8601 (e.g., 2026-01-04T15:30:53.000Z) to RSS RFC 822 format.
    """
    if not iso_date_str:
        return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    try:
        # Remove fractional seconds if present for cleaner parsing
        clean_date = iso_date_str.split(".")[0]
        dt = datetime.strptime(clean_date, "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except Exception:
        return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

def clean_xml_text(text):
    """Escapes special characters for XML safety."""
    if not text:
        return ""
    # Basic XML escaping
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\"", "&quot;").replace("'", "&apos;")
    return text

# ================= MAIN ==================
def fetch_stockwatch_news():
    print(f"Connecting to Stockwatch API: {API_URL} ...")
    try:
        r = requests.get(API_URL, headers=HEADERS_API, timeout=20)
        r.raise_for_status()
        response_json = r.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return

    # Validate response structure
    if not response_json.get("success"):
        print("API reported failure.")
        return

    events_data = response_json.get("data", [])
    if not events_data:
        print("No events found in 'data'.")
        return

    print(f"Found {len(events_data)} events. Generating RSS...")

    items_xml = ""

    for item in events_data:
        # 1. Extract Basic Fields
        uuid = item.get("uuid")
        if not uuid: 
            continue
            
        title = item.get("title", "Corporate Update")
        summary = item.get("summary", "")
        category = item.get("category", "Market News")
        created_at = item.get("createdAt")
        attachment_url = item.get("attachment") # The PDF link
        priority = item.get("priority") # e.g. "trending"

        # 2. Extract Stock Details
        stock_obj = item.get("stock") or {}
        stock_name = stock_obj.get("name")
        stock_code = stock_obj.get("code")  # e.g., PNGJL
        
        # Prefix title with Stock Code if available for quick scanning
        display_title = title
        if stock_code:
            display_title = f"[{stock_code}] {title}"
        elif stock_name:
             display_title = f"[{stock_name}] {title}"

        # 3. Construct the Web Link
        # URL Logic: /news?showModal=true&name={NAME}&title={TITLE}&newsId={UUID}&token={TOKEN}
        token = generate_token(uuid)
        params = {
            "showModal": "true",
            "name": stock_name if stock_name else "Stock",
            "title": title,
            "newsId": uuid,
            "token": token
        }
        # Ensure proper URL encoding
        link = f"{BASE_WEB_URL}?{urllib.parse.urlencode(params)}"

        # 4. Build Description (HTML Content)
        description_parts = []
        
        # Add Trending Tag
        if priority == "trending":
            description_parts.append("<strong>🔥 Trending</strong><br/>")
            
        # Add Summary
        if summary:
            description_parts.append(f"<p>{clean_xml_text(summary)}</p>")
        
        # Add Key Points List
        key_points = item.get("keyPoints", [])
        if key_points and isinstance(key_points, list):
            description_parts.append("<ul>")
            for kp in key_points:
                description_parts.append(f"<li>{clean_xml_text(str(kp))}</li>")
            description_parts.append("</ul>")

        # Add Official Filing Link (PDF)
        if attachment_url:
            description_parts.append(f"<p>📄 <a href=\"{attachment_url}\">Read Official Filing (PDF)</a></p>")

        # Add Footer Metadata
        meta_info = []
        if stock_name: meta_info.append(f"Company: {stock_name}")
        if category: meta_info.append(f"Category: {category}")
        
        description_parts.append(f"<br/><small>{' | '.join(meta_info)}</small>")
        
        full_description = "".join(description_parts)

        # 5. Format Date
        pub_rss = format_pubdate(created_at)

        # 6. Append Item to XML
        items_xml += f"""
    <item>
      <title>{clean_xml_text(display_title)}</title>
      <link>{link}</link>
      <guid isPermaLink="false">{uuid}</guid>
      <pubDate>{pub_rss}</pubDate>
      <category>{clean_xml_text(category)}</category>
      <description><![CDATA[{full_description}]]></description>
    </item>"""

    # Final RSS Wrapper
    rss_feed = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
  <channel>
    <title>Stockwatch - Key Events</title>
    <link>https://www.stockwatch.live/</link>
    <description>Real-time corporate announcements, deals, and financial results.</description>
    <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    <language>en-in</language>
    <atom:link href="{API_URL}" rel="self" type="application/rss+xml" />
    {items_xml}
  </channel>
</rss>"""

    # Write to file
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_feed)
        print(f"Successfully saved RSS feed to: {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error writing file: {e}")

if __name__ == "__main__":
    fetch_stockwatch_news()
