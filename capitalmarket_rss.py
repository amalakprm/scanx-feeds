import requests
import re
from datetime import datetime
from html import unescape

# ================ CONFIG ================
API_URL = "https://api.capitalmarket.com/api/CmLiveNewsHome/A/20"
BASE_ITEM_URL = "https://www.capitalmarket.com/markets/news/live-news"
OUTPUT_FILE = "capital-market-news.xml"

HEADERS_API = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json",
    "Referer": "https://www.capitalmarket.com/"
}
HEADERS_PAGE = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Referer": "https://www.capitalmarket.com/"
}

# ============== HELPERS ================
def create_slug(text: str) -> str:
    if not text:
        return "news"
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9\\s-]', '', text)
    text = re.sub(r'\\s+', '-', text)
    text = text.strip('-')
    return text or "news"

def extract_divtxt(html: str) -> str:
    """
    Extract inner HTML of <div id=\"divtxt\" class=\"memo-content\">...</div>
    """
    m = re.search(
        r'<div\\s+id=[\"\\\']divtxt[\"\\\'][^>]*class=[\"\\\']memo-content[\"\\\'][^>]*>(.*?)</div>',
        html,
        flags=re.I | re.S,
    )
    if not m:
        return ""
    return m.group(1)

def html_to_text(html: str) -> str:
    if not html:
        return ""
    # Replace <br> with space / newline
    html = re.sub(r'<br\\s*/?>', ' ', html, flags=re.I)
    # Remove all other tags
    text = re.sub(r'<[^>]+>', ' ', html)
    text = unescape(text)
    text = re.sub(r'\\s+', ' ', text).strip()
    return text

def first_sentence(text: str) -> str:
    if not text:
        return ""
    parts = re.split(r'(?<=[\\.\\!\\?])\\s+', text, maxsplit=1)
    return parts[0].strip()

# ============== MAIN ================
def fetch_cm_news():
    print("Connecting to Capital Market API...")
    r = requests.get(API_URL, headers=HEADERS_API, timeout=15)
    r.raise_for_status()
    data = r.json()
    if not data.get("success"):
        print("API not successful")
        return

    articles = data.get("data", [])
    if not articles:
        print("No articles")
        return

    items_xml = ""

    for art in articles:
        if not isinstance(art, dict):
            continue

        title = art.get("Heading") or "Market Update"
        sno = art.get("SNO") or "0"
        section = art.get("sectionname") or "Market News"
        subsection = art.get("subsectionname") or ""
        img_url = art.get("IllustrationImage") or ""
        caption = art.get("Caption") or ""

        slug = create_slug(title)
        link = f"{BASE_ITEM_URL}/{slug}/{sno}"

        # ---------- fetch article page & extract body ----------
        body_html = ""
        body_text = ""
        try:
            pr = requests.get(link, headers=HEADERS_PAGE, timeout=15)
            if pr.ok:
                inner = extract_divtxt(pr.text)
                body_html = inner
                body_text = html_to_text(inner)
        except Exception as e:
            print(f"Page fetch failed for {sno}: {e}")

        # summary = first sentence of body, fallback to caption/title
        if body_text:
            summary = first_sentence(body_text)
        else:
            summary = caption or title

        cat_info = section
        if subsection:
            cat_info += f" - {subsection}"

        # DESCRIPTION: first line summary (plain), then optional full text + meta
        description_parts = [summary]

        if body_text and body_text != summary:
            description_parts.append("\\n\\n" + body_text)

        description_parts.append(f"\\n\\n<strong>Category:</strong> {cat_info}<br/>")
        if img_url:
            description_parts.append(
                f'<img src=\"{img_url}\" alt=\"News Image\" style=\"max-width:100%; height:auto;\" />'
            )

        description = "".join(description_parts)

        # pubDate from API date+time
        date_str = art.get("Date", "")
        time_str = art.get("Time", "00:00")
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%d %b %Y %H:%M")
            pub_rss = dt.strftime("%a, %d %b %Y %H:%M:%S +0000")
        except Exception:
            pub_rss = datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

        items_xml += f"""
  <item>
    <title><![CDATA[{title}]]></title>
    <link>{link}</link>
    <guid isPermaLink="false">cm-{sno}</guid>
    <pubDate>{pub_rss}</pubDate>
    <category>{section}</category>
    <description><![CDATA[{description}]]></description>
  </item>"""

    rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:atom="http://www.w3.org/2005/Atom" version="2.0">
  <channel>
    <title>Capital Market - Live News</title>
    <link>{BASE_ITEM_URL}</link>
    <description>Latest market news and updates from Capital Market</description>
    <lastBuildDate>{datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    <language>en-us</language>
    <atom:link href="{BASE_ITEM_URL}" rel="self" type="application/rss+xml" />{items_xml}
  </channel>
</rss>"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(rss_full)

    print(f"Saved RSS with {len(articles)} items -> {OUTPUT_FILE}")

if __name__ == "__main__":
    fetch_cm_news()
