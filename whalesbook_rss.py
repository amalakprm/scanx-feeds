import requests
import xml.etree.ElementTree as ET
from datetime import datetime
import re  # Added for regex operations

API_URL = "https://app1.whalesbook1.shop/published-news-collection/free"
SITE_ROOT = "https://www.whalesbook.com"

def create_slug(text):
    """
    Converts headline to URL-friendly slug while preserving case.
    Replaces % with percent, & with and, removes special chars, 
    and replaces spaces with hyphens.
    """
    if not text:
        return ""
    
    # Specific replacements
    text = text.replace('%', 'percent')
    text = text.replace('&', 'and')
    
    # Remove emojis and special chars (keep letters, numbers, spaces, and hyphens)
    # We do NOT use .lower() because Whalesbook URLs appear to be case-sensitive
    text = re.sub(r'[^\w\s-]', '', text)
    
    # Split by whitespace and join with hyphen
    slug = "-".join(text.split())
    
    # Remove duplicate hyphens
    slug = re.sub(r'-+', '-', slug)
    
    return slug

def create_category_slug(text):
    """
    Converts category types like "Banking/Finance" into "Banking-Finance"
    """
    if not text:
        return "General"
    return text.replace('/', '-').replace(' ', '-')

def fetch_news():
    """
    Fetches the free news collection. 
    Switched to GET as the URL ends in /free and usually requires no payload.
    """
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0 Safari/537.36"
        ),
        "Origin": SITE_ROOT,
        "Referer": f"{SITE_ROOT}/news/English/All",
    }

    print(f"Fetching data from {API_URL}...")
    # Changed to GET request based on the specific URL provided
    resp = requests.get(API_URL, headers=headers, timeout=20)
    resp.raise_for_status()
    
    return resp.json().get("data", [])

def build_article_link(item):
    """
    Constructs the correct Whalesbook URL using the pattern:
    /news/English/{Category}/{Headline-Slug}/{ID}
    """
    # 1. Get required fields
    _id = item.get("_id") or item.get("id")
    headline = item.get("headline")
    news_type = item.get("newsType", "General")

    # 2. Validate
    if not _id or not headline:
        return None

    # 3. Create slugs using the helper functions
    # Note: Language is hardcoded to "English" based on your previous data
    category_slug = create_category_slug(news_type)
    headline_slug = create_slug(headline)

    # 4. Return formatted URL
    return f"{SITE_ROOT}/news/English/{category_slug}/{headline_slug}/{_id}"

def format_pubdate(iso_ts):
    if not iso_ts:
        return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
    try:
        # Handle formats with or without fractional seconds
        if "." in iso_ts:
            iso_ts = iso_ts.split(".")[0] # Strip milliseconds for safety if format varies
        dt = datetime.strptime(iso_ts.replace("Z", ""), "%Y-%m-%dT%H:%M:%S")
        return dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
    except Exception:
        return datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

def generate_rss_xml(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "Whalesbook Financial News"
    ET.SubElement(channel, "link").text = f"{SITE_ROOT}/news/English/All"
    ET.SubElement(channel, "description").text = (
        "Latest Indian and global financial market news from Whalesbook"
    )
    ET.SubElement(channel, "pubDate").text = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    count = 0
    for item in items:
        link = build_article_link(item)
        if not link:
            continue

        entry = ET.SubElement(channel, "item")

        ET.SubElement(entry, "title").text = (
            item.get("headline", "Untitled").strip()
        )
        ET.SubElement(entry, "link").text = link
        ET.SubElement(entry, "guid").text = link

        desc = (item.get("shortDescription") or "").strip()
        ET.SubElement(entry, "description").text = desc

        pub = format_pubdate(item.get("scrappedAt", ""))
        if pub:
            ET.SubElement(entry, "pubDate").text = pub

        image_url = item.get("imageUrl")
        if image_url:
            ET.SubElement(
                entry,
                "enclosure",
                attrib={
                    "url": image_url,
                    "type": "image/jpeg",
                },
            )
        count += 1

    return ET.tostring(
        rss, encoding="utf-8", xml_declaration=True
    ).decode("utf-8")

def main():
    try:
        # No arguments needed for the /free endpoint
        items = fetch_news()
        print(f"Found {len(items)} articles.")
        
        rss_xml = generate_rss_xml(items)

        with open("whalesbook-news.xml", "w", encoding="utf-8") as f:
            f.write(rss_xml)

        print("✅ whalesbook-news.xml generated successfully")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
