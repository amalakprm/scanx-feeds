from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.firefox.service import Service
import json
import re
from datetime import datetime
from html import escape
import time

API_URL = "https://app1.whalesbook1.shop/published-news-collection/free"
OUTPUT_FILE = "whalesbook-news.xml"
BASE_WEB_URL = "https://app1.whalesbook1.shop"

def create_slug(text: str) -> str:
    if not text:
        return "news"
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"\s+", "-", text)
    return text.strip("-") or "news"

def fetch_whalesbook_news():
    print("Starting Firefox browser...")
    
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    
    driver = webdriver.Firefox(
        service=Service(GeckoDriverManager().install()),
        options=firefox_options
    )
    
    try:
        print(f"Loading {API_URL}...")
        driver.get(API_URL)
        time.sleep(3)
        
        page_source = driver.page_source
        print(f"Page loaded, searching for JSON...")
        
        # Look for JSON in page source
        json_match = re.search(r'"data":\s*\[', page_source)
        if json_match:
            # Extract full JSON
            start = page_source.rfind('{', 0, json_match.start())
            depth = 0
            in_string = False
            escape_next = False
            
            for i in range(start, len(page_source)):
                char = page_source[i]
                if escape_next:
                    escape_next = False
                    continue
                if char == '\\':
                    escape_next = True
                    continue
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                if not in_string:
                    if char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            json_str = page_source[start:i+1]
                            payload = json.loads(json_str)
                            break
        
        articles = payload.get("data", [])
        if not articles:
            print("✗ No articles found")
            return
        
        print(f"✓ Found {len(articles)} articles")
        items_xml = ""
        
        for art in articles:
            _id = str(art.get("_id", "0"))
            title = art.get("headline") or "News item"
            short_desc = art.get("shortDescription") or ""
            news_type = art.get("newsType") or "News"
            lang = art.get("languageDisplayed") or "English"
            image_url = art.get("imageUrl")
            
            slug = create_slug(title)
            link = f"{BASE_WEB_URL}/article/{slug}/{_id}"
            
            scrapped_at = art.get("scrappedAt") or ""
            try:
                dt = datetime.fromisoformat(scrapped_at.replace("Z", "+00:00"))
                pub_rss = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
            except:
                pub_rss = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")
            
            desc_parts = [escape(short_desc)] if short_desc else []
            desc_parts.append(f"\n\n<strong>Type:</strong> {escape(news_type)}")
            desc_parts.append(f"<br/><strong>Language:</strong> {escape(lang)}")
            if image_url:
                desc_parts.append(f'<br/><img src="{image_url}" alt="News Image" style="max-width:100%; height:auto;" />')
            
            items_xml += f"""
  <item>
    <title><![CDATA[{title}]]></title>
    <link>{link}</link>
    <guid isPermaLink="false">whalesbook-{_id}</guid>
    <pubDate>{pub_rss}</pubDate>
    ategory>{escape(news_type)}</category>
    <description><![CDATA[{"".join(desc_parts)}]]></description>
  </item>"""
        
        rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  hannel>
    <title>Whalesbook - Free Published News</title>
    <link>{BASE_WEB_URL}</link>
    <description>India's high-quality investment and market news coverage.</description>
    <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    <language>en-us</language>{items_xml}
  </channel>
</rss>"""
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_full)
        
        print(f"✓ Saved RSS with {len(articles)} items -> {OUTPUT_FILE}")
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        driver.quit()

if __name__ == "__main__":
    fetch_whalesbook_news()
