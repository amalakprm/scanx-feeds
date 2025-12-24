import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
import hashlib
import re
import time

NEWS_URL = "https://www.skicapital.net/news/stock-alert"
BASE_URL = "https://www.skicapital.net"
OUT_FILE = "skicapital_news.xml"

# Configuration
MAX_PAGES = 3  # Set to None to fetch all pages
FETCH_FULL_CONTENT = True  # Set False for faster scraping (metadata only)
DELAY_BETWEEN_REQUESTS = 1  # Seconds to wait between requests (be polite)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_html(url: str) -> str:
    """Fetch HTML content from URL"""
    resp = requests.get(url, headers=HEADERS, timeout=20)
    resp.raise_for_status()
    return resp.text


def parse_date_time(date_str: str, time_str: str) -> str:
    """Convert date and time strings to RFC 822 format for RSS"""
    try:
        # Date format: "24-Dec-25", Time format: "08:01"
        dt_str = f"{date_str} {time_str}"
        dt = datetime.strptime(dt_str, "%d-%b-%y %H:%M")

        # Convert to RFC 822 format with IST timezone
        return dt.strftime("%a, %d %b %Y %H:%M:%S") + " +0530"
    except Exception as e:
        print(f"  Warning: Error parsing date/time '{date_str} {time_str}': {e}")
        # Fallback to current time
        return datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S GMT")


def parse_listing(html: str):
    """Parse the listing page to extract article links"""
    soup = BeautifulSoup(html, "html.parser")
    articles = []

    # Find all table rows
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) == 3:
            date_cell = cells[0]
            time_cell = cells[1]
            heading_cell = cells[2]

            # Extract date and time
            date_text = date_cell.get_text(strip=True)
            time_text = time_cell.get_text(strip=True)

            # Skip header row or empty rows
            if date_text in ["DATE", ""] or not date_text:
                continue

            # Find link in heading cell
            link_tag = heading_cell.find("a", href=True)
            if link_tag:
                title = link_tag.get_text(strip=True)
                link = link_tag["href"]

                # Make absolute URL if needed
                if not link.startswith("http"):
                    link = BASE_URL + link

                articles.append({
                    "date": date_text,
                    "time": time_text,
                    "title": title,
                    "link": link
                })

    return articles


def get_pagination_links(html: str) -> list:
    """Extract pagination links from the page"""
    soup = BeautifulSoup(html, "html.parser")
    pagination_links = []

    # Look for pagination links
    # The structure seems to be: << < 1 2 3 ... > >>
    # Find all anchor tags that might be pagination
    for link in soup.find_all("a", href=True):
        href = link["href"]
        # Check if it looks like a pagination link
        # Usually contains page parameter or similar
        if "page=" in href.lower() or re.search(r"/\d+/?$", href):
            if not href.startswith("http"):
                href = BASE_URL + href
            pagination_links.append(href)

    return pagination_links


def fetch_article_content(url: str) -> str:
    """Fetch and extract main content from article page"""
    try:
        html = fetch_html(url)
        soup = BeautifulSoup(html, "html.parser")

        # Look for the article content
        # Method 1: td with text-align: justify
        content_td = soup.find("td", style=lambda s: s and "text-align: justify" in s)

        if content_td:
            # Extract all text, handling <P> tags properly
            content_parts = []
            for element in content_td.descendants:
                if element.name == "b":
                    # Bold text (section headers)
                    text = element.get_text(strip=True)
                    if text:
                        content_parts.append(f"\n{text}\n")
                elif isinstance(element, str):
                    text = element.strip()
                    if text and text not in content_parts:
                        content_parts.append(text)

            content = " ".join(content_parts)

            # Clean up
            content = re.sub(r"\s+", " ", content)  # Multiple spaces
            content = re.sub(r"Powered by.*$", "", content, flags=re.IGNORECASE)

            return content.strip()

        return ""
    except Exception as e:
        print(f"  Warning: Error fetching content from {url}: {e}")
        return ""


def rss_item(channel, art, include_full_content=True):
    """Create RSS item element"""
    title = art["title"]
    link = art["link"]
    date_str = art["date"]
    time_str = art["time"]

    item = ET.SubElement(channel, "item")
    ET.SubElement(item, "title").text = title
    ET.SubElement(item, "link").text = link

    # Fetch full article content if requested
    description = ""
    if include_full_content:
        description = fetch_article_content(link)
        time.sleep(DELAY_BETWEEN_REQUESTS)  # Be polite

    if not description:
        description = f"Posted: {date_str} at {time_str}"

    ET.SubElement(item, "description").text = description

    # Use link as GUID (permanent link)
    ET.SubElement(item, "guid", isPermaLink="true").text = link

    # Parse and add publication date
    pub_date = parse_date_time(date_str, time_str)
    ET.SubElement(item, "pubDate").text = pub_date

    # Optional: Add category
    ET.SubElement(item, "category").text = "Stock Alert"


def build_rss(articles, include_full_content=True):
    """Build RSS feed XML"""
    rss = ET.Element("rss", version="2.0")
    channel = ET.SubElement(rss, "channel")

    ET.SubElement(channel, "title").text = "SKI Capital – Stock Alert News"
    ET.SubElement(channel, "link").text = NEWS_URL
    ET.SubElement(channel, "description").text = (
        "Stock alert news from SKI Capital Services - Indian stock market updates"
    )
    ET.SubElement(channel, "language").text = "en-IN"
    ET.SubElement(channel, "lastBuildDate").text = datetime.now(
        timezone.utc
    ).strftime("%a, %d %b %Y %H:%M:%S GMT")

    print(f"\nBuilding RSS items ({len(articles)} total)...")
    for i, art in enumerate(articles, 1):
        if include_full_content:
            print(f"  [{i}/{len(articles)}] {art['title'][:60]}...")
        rss_item(channel, art, include_full_content)

    tree = ET.ElementTree(rss)
    ET.indent(tree, space="  ")  # Pretty print
    tree.write(OUT_FILE, encoding="utf-8", xml_declaration=True)


def main():
    print("="*60)
    print("SKI Capital Stock Alert Scraper")
    print("="*60)
    print(f"Source: {NEWS_URL}")
    print(f"Max pages: {MAX_PAGES if MAX_PAGES else 'All'}")
    print(f"Full content: {FETCH_FULL_CONTENT}")
    print("="*60)

    all_articles = []
    page_num = 1

    # Fetch first page
    print(f"\nFetching page {page_num}...")
    html = fetch_html(NEWS_URL)
    articles = parse_listing(html)
    print(f"  Found {len(articles)} articles")
    all_articles.extend(articles)

    # For now, we'll just fetch the first page
    # Pagination in ASP.NET sites often requires POST with ViewState
    # which is complex. If you need pagination, we can enhance this.

    if not all_articles:
        print("\nNo articles found!")
        return

    # Remove duplicates based on link
    seen_links = set()
    unique_articles = []
    for art in all_articles:
        if art["link"] not in seen_links:
            seen_links.add(art["link"])
            unique_articles.append(art)

    print(f"\nTotal unique articles: {len(unique_articles)}")
    print("\nSample articles:")
    for art in unique_articles[:5]:
        print(f"  [{art['date']} {art['time']}] {art['title'][:65]}...")

    # Build RSS feed
    build_rss(unique_articles, FETCH_FULL_CONTENT)

    print(f"\n{'='*60}")
    print(f"✓ RSS feed saved to: {OUT_FILE}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
