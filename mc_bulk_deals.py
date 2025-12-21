import requests
import os
from datetime import datetime

# ================= CONFIG =================
API_URL = "https://www.moneycontrol.com/master-page/api/v1/bulk-deal"
OUTPUT_FILE = "bulk-deals.xml"

# Moneycontrol needs a basic User-Agent to respond
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json"
}

def fetch_mc_deals():
    print(f"Fetching Bulk Deals from Moneycontrol...")
    try:
        response = requests.get(API_URL, headers=HEADERS, timeout=15)
        response.raise_for_status()
        raw_data = response.json()
        
        # The data is usually under data -> bulk_deals and data -> block_deals
        data = raw_data.get('data', {})
        bulk_list = data.get('bulk_deals', [])
        block_list = data.get('block_deals', [])
        all_deals = bulk_list + block_list

        items_xml = ""
        for deal in all_deals:
            # Extract fields (mapping based on MC JSON structure)
            symbol = deal.get('symbol', 'N/A')
            company = deal.get('company_name', 'Unknown')
            client = deal.get('client_name', 'Unknown')
            action = deal.get('deal_type', 'TRADE') # BUY/SELL
            qty = deal.get('quantity', '0')
            price = deal.get('price', '0')
            deal_date = deal.get('deal_date', '')
            
            title = f"{action}: {symbol} ({qty} shares) by {client}"
            # Direct link to Moneycontrol stock page
            link = f"https://www.moneycontrol.com/india/stockpricequote/stocks/{symbol}"
            
            description = f"""
            <strong>Company:</strong> {company} ({symbol})<br/>
            <strong>Action:</strong> {action}<br/>
            <strong>Client:</strong> {client}<br/>
            <strong>Quantity:</strong> {qty}<br/>
            <strong>Price:</strong> ₹{price}<br/>
            <strong>Date:</strong> {deal_date}
            """

            items_xml += f"""
    <item>
      <title><![CDATA[{title}]]></title>
      <link>{link}</link>
      <guid isPermaLink="false">{symbol}-{deal_date}-{qty}-{price}</guid>
      <description><![CDATA[{description}]]></description>
      <pubDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</pubDate>
    </item>"""

        rss_full = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Live Bulk &amp; Block Deals (NSE/BSE)</title>
    <link>https://www.moneycontrol.com</link>
    <description>Real-time feed of large market transactions.</description>
    <lastBuildDate>{datetime.now().strftime("%a, %d %b %Y %H:%M:%S +0000")}</lastBuildDate>
    {items_xml}
  </channel>
</rss>"""

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(rss_full)
        print(f"Successfully wrote {len(all_deals)} deals to {OUTPUT_FILE}")

    except Exception as e:
        print(f"Error fetching MC deals: {e}")

if __name__ == "__main__":
    fetch_mc_deals()
