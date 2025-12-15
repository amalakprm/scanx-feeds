# ================= CONFIG =================
$apiUrl   = "https://news-live.dhan.co/news/getlatestarticlelist"
$imgBase  = "https://news-images.dhan.co/"
$newsBase = "https://scanx.trade/stock-market-news/stocks/"

# Output in SAME folder as this .ps1 file
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rssPath   = Join-Path $scriptDir "dhan-scanx-news.xml"

# ================= FETCH DATA =================
$res = Invoke-WebRequest `
  -Uri $apiUrl `
  -Method POST `
  -Headers @{
    "accept"       = "application/json, text/plain, */*"
    "content-type" = "application/json"
    "origin"       = "https://scanx.trade"
    "auth"         = "null"
  } `
  -Body '{"category":"all","subcategory":"all"}'

$data = $res.Content | ConvertFrom-Json
$articles = $data.data.Articlelist.Articles

# ================= BUILD RSS ITEMS =================
$itemsXml = $articles | ForEach-Object {

    # Create SEO slug from title
    $slug = $_.articletitle.ToLower()
    $slug = $slug -replace '[^a-z0-9\s-]', ''
    $slug = $slug -replace '\s+', '-'
    $slug = $slug.Trim('-')

    # Correct ScanX article URL
    $link = "$newsBase$slug/$($_.id)"

    $image = "$imgBase$($_.imageurl)"

@"
  <item>
    <title><![CDATA[$($_.articletitle)]]></title>
    <link>$link</link>
    <guid isPermaLink="true">$link</guid>
    <description><![CDATA[
      <img src="$image" /><br/>
    ]]></description>
  </item>
"@
} | Out-String

# ================= FINAL RSS =================
$rss = @"
<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title><![CDATA[Dhan / ScanX Latest News (Personal)]]></title>
    <link>https://scanx.trade/stock-market-news</link>
    <description><![CDATA[Personal wrapper around Dhan/ScanX news.]]></description>
$itemsXml
  </channel>
</rss>
"@

# ================= WRITE FILE =================
$rss | Out-File -FilePath $rssPath -Encoding utf8
Write-Host "RSS written to $rssPath"
