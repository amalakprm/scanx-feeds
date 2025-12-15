import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import hashlib

NEWS_URL = "https://www.marketsmojo.com/news"
OUT_FILE = "marketsmojo_news.xml"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_html(url: str) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_cards(html: str):
    soup = BeautifulSoup(html, "html.parser")
    container = soup.find(id="news-results-container")
    if not container:
        return []

    articles = []
    for card in container.select("div.news-article-card"):
        # first anchor inside card gives canonical article URL
        a = card.find("a", href=True)
        if not a:
            continue
        link = a["href"].strip()

        # title
        title_el = card.select_one(".card-title")
        title = title_el.get_text(strip=True) if title_el else ""

        # description/snippet
        body_p = card.select_one(".card-body p")
        desc = body_p.get_text(" ", strip=True) if body_p else ""

        # optional time text like "2 hours ago"
        time_el = card.select_one(".article-card-footer div")
        time_text = time_el.get_text(strip=True) if time_el else ""

        if not title or not link:
            continue

        articles.append(
            {
                "title": title,
                "link": link,
                "description": desc,
                "time_text": time_text,
            }
        )

    return articles


def rss_item(channel, art):
    title = art["title"]
    link = art["link"]
    desc = art["description"]
    time_text = art.get("time_text")

    if time_text:
        desc = f"{desc}\nTime: {time_text}"

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = link
    ET.SubElement(item, "description").text = desc

    guid_src = (title + link).encode("utf-8", errors="ignore")
    ET.SubElement(item, "guid").text = hashlib.md5(guid_src).hexdigest()

    # no absolute timestamp on page; use build time
    ET.SubElement(item, "pubDate").text = datetime.now(timezone.utc).strftime(
        "%a, %d %b %Y %H:%M:%S GMT"
    )


def build_rss(articles):
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "MarketsMojo – News (homepage)"
    ET.SubElement(channel, "link").text = NEWS_URL
    ET.SubElement(channel, "description").text = (
        "RSS scraped from https://www.marketsmojo.com/news"
    )
    ET.SubElement(channel, "language").text = "en-IN"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(
        timezone.utc
    ).strftime("%a, %d %b %Y %H:%M:%S GMT")

    for art in articles:
        rss_item(channel, art)

    tree = ET.ElementTree(rss)
    tree.write(OUT_FILE, encoding="utf-8", xml_declaration=True)


def main():
    print("Fetching:", NEWS_URL)
    html = fetch_html(NEWS_URL)
    print("Parsing cards…")
    arts = parse_cards(html)
    print("Found", len(arts), "articles.")
    if not arts:
        return
    build_rss(arts)
    print("RSS written to", OUT_FILE)


if __name__ == "__main__":
    main()
