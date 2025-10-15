# Retail Product Scraper

Production-grade web scraper for Target, Costco, HomeGoods, and TJ Maxx. Extracts complete product data with proof of completeness.

## Features

- **Multi-method enumeration** for proof of completeness
- **Per-retailer scrapers** optimized for each site's structure
- **Home network first** with automatic proxy escalation
- **Browser automation** with stealth detection bypass
- **Async/concurrent** processing optimized for 32GB RAM
- **Image URL extraction** (no downloads)
- **Comprehensive exports** (JSON, CSV, manifests)

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

## Configuration

Edit `config.py` to customize:

- `zip_code`: Your location for pricing (default: 90210)
- `concurrency`: Concurrent scrapers per retailer
- `proxy.datacenter_pool`: Add your proxy URL if you have one
- `delays_ms`: Rate limiting delays

## Usage

### Full Scrape (All Retailers)

```bash
python main.py
```

### Specific Retailers

```bash
python main.py --retailers target costco
```

### Test Mode

```bash
python main.py --test
```

Test mode limits enumeration for quick validation.

## How It Works

### 1. Enumeration

Each retailer uses multiple methods to discover all products:

- **Target**: Sitemap parsing + GraphQL API validation
- **Costco**: Sitemap + category pagination
- **HomeGoods/TJ Maxx**: Category tree crawling

### 2. Scraping

- **Concurrent workers**: 8-25 per retailer (configured by site)
- **Rate limiting**: 150-500ms jitter between requests
- **Auto-proxy escalation**: Switches if block rate >2%
- **Retry logic**: 3 attempts with exponential backoff

### 3. Data Extraction

Captures for each product:
- Product ID, URL, title, brand, category
- Current price, compare-at price
- Availability, description
- Image URLs (array)
- Ratings, shipping (best effort)
- Variants, specifications

### 4. Exports

Generated in `exports/` directory:

- `export_{retailer}_{timestamp}.json`: Full product data
- `export_{retailer}_{timestamp}.csv`: Flattened CSV
- `completeness_report_{timestamp}.json`: Enumeration proof
- `variance_analysis_{timestamp}.txt`: Method comparison
- `coverage_matrix_{timestamp}.csv`: Success/failure breakdown

## Proof of Completeness

Multi-method enumeration with cross-validation:

1. Primary: Sitemap parsing (authoritative source)
2. Secondary: Category crawling (captures unlisted items)
3. Validation: Methods must agree within ±2%

Reports include:
- Count from each method
- Variance analysis
- Coverage statistics (≥98% target)

## Proxy Escalation

**Default**: Runs on home network

**Auto-switches to proxy when:**
- Block rate >2% in 5-minute window, OR
- 10+ consecutive failures (403/429/CAPTCHA)

**To add proxy credentials:**
```python
# config.py
'proxy': {
    'datacenter_pool': 'http://username:password@proxy.example.com:8000'
}
```

## Output Files

```
exports/
  ├── export_target_20241014_123456.json
  ├── export_target_20241014_123456.csv
  ├── export_costco_20241014_123456.json
  ├── export_costco_20241014_123456.csv
  ├── completeness_report_20241014_123456.json
  ├── variance_analysis_20241014_123456.txt
  └── coverage_matrix_20241014_123456.csv

manifests/
  ├── manifest_target_20241014_123456.csv
  ├── manifest_target_20241014_123456.sha256
  ├── manifest_costco_20241014_123456.csv
  └── manifest_costco_20241014_123456.sha256

scraper_data.db (SQLite database)
```

## Performance

Optimized for 32GB RAM machine:

- **Browser pool**: Up to 80 concurrent Playwright instances
- **Memory management**: Auto-cleanup every 15 minutes
- **Throughput**: 30-50 products/minute (varies by retailer)
- **Full scrape**: Several hours depending on catalog size

## Monitoring

Real-time terminal output shows:

```
[Home Network Mode] ██████████░░░░░░ 62.5% | Success: 1,234 | Failed: 12 | Blocked: 3 | Block Rate: 0.2% | Speed: 45 items/min
```

## Notes

- **Costco**: Public data only (no membership login)
- **HomeGoods/TJ Maxx**: High 404 rate expected (inventory churn)
- **Target**: Uses GraphQL API interception for best data
- **Images**: URLs only, no file downloads

## Success Criteria

- ≥98% of enumerated products scraped successfully
- Multiple enumeration methods agree within ±2%
- Block rate <2% (or successfully switched to proxies)
- All required fields populated (product_id, url, title, price)

## Troubleshooting

**High block rate?**
- Increase delays in `config.py`
- Add proxy credentials
- Reduce concurrency

**Cloudflare challenges?**
- Automatically handled by stealth browser
- May need proxy for Costco if persists

**Memory issues?**
- Reduce `browser_pool_size` in config
- Decrease concurrency limits

**Missing data?**
- Check `errors` table in database
- Review `variance_analysis.txt` for enumeration gaps

