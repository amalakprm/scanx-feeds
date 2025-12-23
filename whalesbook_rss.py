import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import re
import json

# --- CONFIGURATION ---
API_URL = "https://app1.whalesbook1.shop/published-news-collection/free"
SITE_ROOT = "https://www.whalesbook.com"

def create_slug(text):
    if not text: return ""
    text = text.replace('%', 'percent').replace('&', 'and')
    text = re.sub(r'[^\w\s-]', '', text)
    slug = "-".join(text.split())
    slug = re.sub(r'-+', '-', slug)
    return slug

def create_category_slug(text):
    if not text: return "General"
    return text.replace('/', '-').replace(' ', '-')

def build_article_link(item):
    _id = item.get("_id") or item.get("id")
    headline = item.get("headline")
    news_type = item.get("newsType", "General")
    
    if not _id or not headline: return None
    
    category_slug = create_category_slug(news_type)
    headline_slug = create_slug(headline)
    
    return f"{SITE_ROOT}/news/English/{category_slug}/{headline_slug}/{_id}"

def fetch_news():
    print(f"Fetching data from {API_URL}...")
    
    # Payload matching your original successful request structure
    payload = {
        "date": datetime.utcnow().strftime("%Y-%m-%d"),
        "page": 1,
        "limit": 40,
        "sector": "All",
        "language": "English"
    }

    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Origin": SITE_ROOT,
        "Referer": f"{SITE_ROOT}/news/English/All",
    }

    try:
        # SWITCHED BACK TO POST
        resp = requests.post(API_URL, json=payload, headers=headers, timeout=30)
        
        # DEBUGGING: Check if request failed
        if resp.status_code != 200:
            print(f"⚠️ Request failed with Status Code: {resp.status_code}")
            print(f"⚠️ Response Text: {resp.text[:500]}") # Print first 500 chars to see error
            return []

        return resp.json().get("data", [])

    except json.JSONDecodeError:
        print("❌ Error: Server did not return JSON.")
        print(f"Response Text: {resp.text[:500]}")
        return []
    except Exception as e:
        print(f"❌ Connection Error: {e}")
        return []

def format_pubdate(iso_ts):
    if not iso_ts: return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    try:
        if "." in iso_ts: iso_ts = iso_ts.split(".")[0]
        dt = datetime.strptime(iso_ts.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except:
        return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

def generate_rss_xml(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Whalesbook Financial News"
    ET.SubElement(channel, "link").text = f"{SITE_ROOT}/news/English/All"
    ET.SubElement(channel, "description").text = "Latest Indian and global financial market news"
    ET.SubElement(channel, "pubDate").text = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    count = 0
    for item in items:
        link = build_article_link(item)
        if not link: continue

        entry = ET.SubElement(channel, "item")
        ET.SubElement(entry, "title").text = item.get("headline", "Untitled").strip()
        ET.SubElement(entry, "link").text = link
        ET.SubElement(entry, "guid").text = link
        ET.SubElement(entry, "description").text = (item.get("shortDescription") or "").strip()
        
        pub = format_pubdate(item.get("scrappedAt", ""))
        if pub: ET.SubElement(entry, "pubDate").text = pub

        image_url = item.get("imageUrl")
        if image_url:
            ET.SubElement(entry, "enclosure", attrib={"url": image_url, "type": "image/jpeg"})
        count += 1
    
    print(f"Generated RSS with {count} items.")
    return ET.tostring(rss, encoding="utf-8", xml_declaration=True).decode("utf-8")

def main():
    items = fetch_news()
    if items:
        rss_xml = generate_rss_xml(items)
        with open("whalesbook-news.xml", "w", encoding="utf-8") as f:
            f.write(rss_xml)
        print("✅ whalesbook-news.xml generated successfully")
    else:
        print("❌ No items fetched. XML not generated.")

if __name__ == "__main__":
    main()
