import requests
import xml.etree.ElementTree as ET
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

BASE_URL = "https://www.skicapital.net"
NEWS_LIST_URL = "https://www.skicapital.net/news/news-list.aspx"


def fetch_news():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    resp = requests.get(NEWS_LIST_URL, headers=headers, timeout=20)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    items = []

    # SKI Capital uses anchor links for news items
    for a in soup.select("a[href*='news-details']"):
        title = a.get_text(strip=True)
        href = a.get("href")

        if not title or not href:
            continue

        full_url = urljoin(BASE_URL, href)

        items.append({
            "title": title,
            "link": full_url
        })

    return items


def generate_rss(items):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "SKI Capital – News"
    ET.SubElement(channel, "link").text = NEWS_LIST_URL
    ET.SubElement(channel, "description").text = "Latest news and updates from SKI Capital"
    ET.SubElement(channel, "pubDate").text = datetime.utcnow().strftime(
        "%a, %d %b %Y %H:%M:%S +0000"
    )

    for item in items:
        entry = ET.SubElement(channel, "item")
        ET.SubElement(entry, "title").text = item["title"]
        ET.SubElement(entry, "link").text = item["link"]
        ET.SubElement(entry, "guid").text = item["link"]

    return ET.tostring(
        rss, encoding="utf-8", xml_declaration=True
    ).decode("utf-8")


def main():
    news_items = fetch_news()

    if not news_items:
        print("⚠️ No news items found")
        return

    rss_xml = generate_rss(news_items)

    with open("skicapital-news.xml", "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print("✅ skicapital-news.xml generated successfully")


if __name__ == "__main__":
    main()
