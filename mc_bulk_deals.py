import requests
import time
import os
from datetime import datetime

# ================= CONFIG =================
BASE_URL = "https://www.nseindia.com"
# Correct endpoint from the documentation you shared
API_URL = "https://www.nseindia.com/api/snapshot-bulk-block-deal"
OUTPUT_FILE = "bulk-deals.xml"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/report-details/display-bulk-and-block-deals"
}

def get_deals():
    session = requests.Session()
    session.headers.update(HEADERS)

    try:
        # STEP 1: Handshake
        # We must hit the home page to get the 'nsit' and 'nseappid' cookies
        print("Bypassing NSE security (Session Handshake)...")
        session.get(BASE_URL, timeout=15)
        time.sleep(2) # Brief pause to mimic a human browser

        # STEP 2: Fetch the data
        print(f"Fetching Live Deals from: {API_URL}")
        response = session.get(API_URL, timeout=15)
        
        if response.status_code != 200:
            print(f"NSE returned status {response.status_code}. Retrying...")
            return None

        data = response.json()
        bulk_deals = data.get('bulkDeals', [])
        block_deals = data.get('blockDeals', [])
        all_deals = bulk_deals + block_deals
        
        print(f"Found {len(all_deals)} live deals.")
        return all_deals

    except Exception as e:
        print(f"Error connecting to NSE: {e}")
        return None

def build_rss(deals):
    items_xml = ""
    for deal in deals:
        symbol = deal.get('symbol', 'N/A')
        client = deal.get('clientName', 'Unknown')
        action = deal.get('buySell', 'TRADE')
        qty = deal.get('quantity', '0')
        price = deal.get('tradePrice', '0')
        date = deal.get('dealDate', '')
        
        title = f"{action}: {symbol} ({qty} qty) by {client}"
        link = f"https://www.nseindia.com/get-quotes/equity?symbol={symbol}"
        
        description = f"""
        <strong>Symbol:</strong> {symbol}<br/>
        <strong>Party:</strong> {client}<br/>
        <strong>Action:</strong> {action}<br/>
        <strong>Quantity:</strong> {qty}<br/>
        <strong>Price:</strong> ₹{price}<br/>
        <strong>Date:</strong> {date}
        """

        items_xml += f"""
    <item>
      <title><![CDATA[{title}]]></title>
      <link>{link}</link>
      <guid isPermaLink="false">{symbol}-{date}-{qty}-{price}</guid>
      <pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
      <description><![CDATA[{description}]]></description>
    </item>"""

    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>NSE Live Bulk &amp; Block Deals</title>
    <link>https://www.nseindia.com</link>
    <description>Live feed of large transactions on NSE.</description>
    {items_xml}
  </channel>
</rss>"""

if __name__ == "__main__":
    deals = get_deals()
    if deals:
        rss_content = build_rss(deals)
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_content)
        print(f"Successfully wrote {OUTPUT_FILE}")
    else:
        print("No data fetched. NSE might be blocking the GitHub IP.")
