# ScanX Feeds (auto-updating)

This repository automatically generates **7 RSS feeds** from ScanX:

- `scanx_stock_news.xml`
- `scanx_corporate_actions.xml`
- `scanx_earnings.xml`
- `scanx_orders_deals.xml`
- `scanx_global.xml`
- `scanx_markets.xml`
- `scanx_ipo_news.xml`

A GitHub Action runs **every 3 hours** and refreshes the feeds.

## How to use (for Amal on Windows, 10th-standard level)

1. Create a new public repo on GitHub, for example: `scanx-feeds`.
2. Download this project as a ZIP and unzip it.
3. Upload all files (including the `.github` folder) into that repo:
   - On GitHub: Code → "Add file" → "Upload files"
   - Drag all files and folders from the unzipped folder into the browser.
   - Click "Commit changes".
4. Go to the **Actions** tab, enable workflows if GitHub shows a warning.
5. Open the workflow "Update ScanX RSS feeds" and click "Run workflow" once.

After the first run:

- You will see `scanx_*.xml` files in the repository root.

## Enable GitHub Pages (to get URLs for Feeder)

1. Go to **Settings → Pages** in the repo.
2. Under "Source", choose:
   - Branch: `main`
   - Folder: `/ (root)`
3. Click "Save".

After a short time, GitHub Pages will be live, for example:

- `https://<your-username>.github.io/scanx-feeds/scanx_orders_deals.xml`
- `https://<your-username>.github.io/scanx-feeds/scanx_markets.xml`

(Replace `<your-username>` and `scanx-feeds` with your actual GitHub username and repo name.)

## Add feeds to your mobile RSS reader (Feeder)

In Feeder on your phone, add a new feed using the URL. Example:

- Orders & Deals:
  `https://<your-username>.github.io/scanx-feeds/scanx_orders_deals.xml`

- Markets:
  `https://<your-username>.github.io/scanx-feeds/scanx_markets.xml`

…and so on for the other categories.

## How it works internally (simple)

- `generate_scanx_feeds.py`:
  - downloads each ScanX category page,
  - finds all `a.article-card` elements,
  - extracts title, link, text, time,
  - writes XML files `scanx_*.xml`.
- `.github/workflows/update_scanx.yml`:
  - runs every 3 hours,
  - calls `python generate_scanx_feeds.py`,
  - commits any changes to the repo.

You do **not** need to run anything from your computer after setup.
GitHub will keep the feeds fresh automatically.
