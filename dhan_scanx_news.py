import re
import sys
import requests

API_URL = "https://news-live.dhan.co/news/getlatestarticlelist"
IMG_BASE = "https://news-images.dhan.co/"
NEWS_BASE = "https://scanx.trade/stock-market-news/stocks/"
OUT_FILE = "dhan-scanx-news.xml"
TIMEOUT = 20

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://scanx.trade",
    "auth": "null",
}

PAYLOAD = {"category": "all", "subcategory": "all"}


def slugify(title: str) -> str:
    s = title.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s


def fetch_articles():
    r = requests.post(API_URL, headers=HEADERS, json=PAYLOAD, timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    return data["data"]["Articlelist"]["Articles"]


def build_rss(articles):
    items = []
    for a in articles:
        title = a.get("articletitle", "").strip()
        if not title:
            continue

        slug = slugify(title)
        article_id = a.get("id")
        link = f"{NEWS_BASE}{slug}/{article_id}"

        imageurl = (a.get("imageurl") or "").lstrip("/")
        image = f"{IMG_BASE}{imageurl}" if imageurl else ""

        # Keep it close to your PS logic: title in CDATA, description contains <img> in CDATA
        desc = f'<img src="{image}" /><br/>' if image else ""

        items.append(
            "\n".join(
                [
                    "  <item>",
                    f"    <title><![CDATA[{title}]]></title>",
                    f"    <link>{link}</link>",
                    f'    <guid isPermaLink="true">{link}</guid>',
                    "    <description><![CDATA[",
                    f"      {desc}",
                    "    ]]></description>",
                    "  </item>",
                ]
            )
        )

    items_xml = "\n".join(items)

    return "\n".join(
        [
            '<?xml version="1.0" encoding="UTF-8"?>',
            '<rss version="2.0">',
            "  <channel>",
            "    <title><![CDATA[Dhan / ScanX Latest News (Personal)]]></title>",
            "    <link>https://scanx.trade/stock-market-news</link>",
            "    <description><![CDATA[Personal wrapper around Dhan/ScanX news.]]></description>",
            items_xml,
            "  </channel>",
            "</rss>",
        ]
    )


def main():
    try:
        articles = fetch_articles()
        rss = build_rss(articles)
        with open(OUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss)
        print(f"Wrote {OUT_FILE} ({len(articles)} articles fetched)")
    except Exception as e:
        print(f"Failed: {e}", file=sys.stderr)
        print("Keeping previous XML (fail-soft)")


if __name__ == "__main__":
    main()
