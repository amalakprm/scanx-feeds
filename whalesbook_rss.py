import requests
import json
from datetime import datetime
import xml.etree.ElementTree as ET
from io import StringIO

url = "https://app1.whalesbook1.shop/published-news-collection/free"

def fetch_news(page=1, limit=20, sector="All", language="English"):
    payload = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "page": page,
        "limit": limit,
        "sector": sector,
        "language": language
    }
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    resp = requests.post(url, json=payload, headers=headers)
    return resp.json().get('data', [])

def generate_rss(news_items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")
    ET.SubElement(channel, "title").text = "Whalesbook Financial News"
    ET.SubElement(channel, "link").text = "https://www.whalesbook.com/news/English/All"
    ET.SubElement(channel, "description").text = "Latest Indian financial market news"
    ET.SubElement(channel, "pubDate").text = datetime.now().strftime("%a, %d %b %Y %H:%M:%S %z")
    
    for item in news_items[-20:]:  # Last 20 items
        title = item.get('headline', 'No title')
        desc = item.get('shortDescription', '')[:500] + "..."
        link = f"https://www.whalesbook.com/news/English/{item.get('newsType', 'All')}/{title.replace(' ', '-')}/{item.get('id')}"
        pubdate = item.get('scrappedAt', '')
        
        entry = ET.SubElement(channel, "item")
        ET.SubElement(entry, "title").text = title
        ET.SubElement(entry, "link").text = link
        ET.SubElement(entry, "description").text = desc
        ET.SubElement(entry, "pubDate").text = pubdate
        if img := item.get('imageUrl'):
            ET.SubElement(entry, "enclosure", url=img, type="image/jpeg")
    
    return ET.tostring(rss, encoding='unicode', method='xml')

# Fetch latest news and generate RSS
news = fetch_news()
rss_xml = generate_rss(news)

print("RSS Feed Generated Successfully:")
print(rss_xml)

# Save to file
with open('whalesbook_news.rss', 'w') as f:
    f.write(rss_xml)
print("\nRSS saved to whalesbook_news.rss")
