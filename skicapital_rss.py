import requests

# ===== TEMP DEBUG START (REMOVE AFTER TEST) =====
def debug_fetch_detailed_news():
    url = "https://www.skicapital.net/news/detailed-news.aspx"

    r = requests.get(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
        },
        timeout=20
    )

    print("STATUS:", r.status_code)
    print("RESPONSE LENGTH:", len(r.text))
    print("----- FIRST 1000 CHARS START -----")
    print(r.text[:1000])
    print("----- FIRST 1000 CHARS END -----")


if __name__ == "__main__":
    debug_fetch_detailed_news()
# ===== TEMP DEBUG END =====
