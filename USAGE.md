# Usage Guide - Retail Product Scraper

## Quick Start

### 1. Setup (First Time)

```bash
# Run setup script
./setup.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

### 2. Configure

Edit `config.py`:

```python
CONFIG = {
    'zip_code': '90210',  # ← Change to your ZIP code
    
    # Add proxy if you have one:
    'proxy': {
        'datacenter_pool': 'http://user:pass@proxy.example.com:8000'
    }
}
```

### 3. Test Setup

```bash
python test_setup.py
```

This validates:
- All imports work
- Database can be created
- Playwright browser works
- Directories are created

### 4. Run Test Mode

Start with a limited test to validate everything works:

```bash
python main.py --test
```

This will:
- Enumerate limited products (5 sitemaps, 10 categories)
- Scrape a small sample
- Generate test exports

### 5. Run Full Scrape

Once test mode succeeds:

```bash
# All retailers
python main.py

# Specific retailers only
python main.py --retailers target costco
```

## What Happens During Scrape

### Phase 1: Enumeration (per retailer)

```
===============================================================================
ENUMERATION: TARGET
===============================================================================

[target] Method 1: Sitemap enumeration...
  Found 5 sitemap files to parse...
    Parsed sitemap 1/5: 10000 URLs
    Parsed sitemap 2/5: 10000 URLs
    ...
  ✓ Found 45,231 products from sitemap

✓ Total unique products: 45,231
✓ Exported manifest: 45,231 URLs, hash: 8a3b4f5c...
```

### Phase 2: Scraping

```
===============================================================================
SCRAPING: TARGET
===============================================================================

[Home Network Mode] ████████████░░░░ 75.2% | Success: 34,024 | Failed: 15 | Blocked: 8 | Block Rate: 0.02% | Speed: 42 items/min
```

If block rate exceeds 2%:

```
================================================================================
⚠️  PROXY ESCALATION: Block rate threshold exceeded at 2024-10-14 12:34:56
================================================================================

[Proxy Mode] ████████████████ 100% | Success: 45,189 | Failed: 42 | Blocked: 0 | Block Rate: 0.0% | Speed: 38 items/min
```

### Phase 3: Export

```
===============================================================================
EXPORTING DATA
===============================================================================

✓ Exported 45,189 items to exports/export_target_20241014_123456.json
✓ Exported 45,189 items to exports/export_target_20241014_123456.csv

✓ Completeness package exported:
  - exports/completeness_report_20241014_123456.json
  - exports/variance_analysis_20241014_123456.txt

✓ Coverage matrix exported: exports/coverage_matrix_20241014_123456.csv
```

### Phase 4: Summary

```
===============================================================================
SCRAPE SUMMARY
===============================================================================

TARGET
  Attempted: 45,231
  Success: 45,189 (99.91%)
  Failed: 42
  Block Rate: 0.02%
  Proxy Used: No
  Meets Target (≥98%): ✓
```

## Output Files Explained

### Product Exports

**JSON Format** (`export_target_20241014_123456.json`):
```json
[
  {
    "product_id": "12345678",
    "retailer": "target",
    "product_url": "https://www.target.com/p/-/A-12345678",
    "title": "Product Name",
    "brand": "Brand Name",
    "category": "Category > Subcategory",
    "price_current": 19.99,
    "price_compare_at": 24.99,
    "currency": "USD",
    "availability": "in_stock",
    "description": "Product description...",
    "image_urls": [
      "https://target.scene7.com/is/image/Target/image1",
      "https://target.scene7.com/is/image/Target/image2"
    ],
    "ratings_average": 4.5,
    "ratings_count": 123,
    "specifications": {},
    "scraped_at": "2024-10-14T12:34:56"
  }
]
```

**CSV Format** (`export_target_20241014_123456.csv`):

Same data, flattened. Arrays like `image_urls` are JSON strings in CSV.

### Manifests

**Manifest File** (`manifest_target_20241014_123456.csv`):
```
https://www.target.com/p/-/A-12345678
https://www.target.com/p/-/A-87654321
...
```

**Hash File** (`manifest_target_20241014_123456.sha256`):
```
8a3b4f5c2d1e6789abcdef0123456789abcdef0123456789abcdef0123456789
```

This proves the manifest hasn't been altered.

### Completeness Report

**Completeness Report** (`completeness_report_20241014_123456.json`):
```json
{
  "target": {
    "retailer": "target",
    "timestamp": "2024-10-14T12:34:56",
    "enumeration_methods": {
      "sitemap": {
        "count": 45231,
        "timestamp": "2024-10-14T11:23:45",
        "notes": "Parsed from https://www.target.com/sitemap_products.xml"
      }
    },
    "variance_analysis": {
      "max_count": 45231,
      "min_count": 45231,
      "variance_percent": 0.0,
      "within_threshold": true
    }
  }
}
```

### Variance Analysis

**Variance Analysis** (`variance_analysis_20241014_123456.txt`):
```
VARIANCE ANALYSIS - Multi-Method Enumeration
================================================================================

TARGET
----------------------------------------
  sitemap: 45,231 products

  Variance: 0.00%
  Within ±2% threshold: True
```

### Coverage Matrix

**Coverage Matrix** (`coverage_matrix_20241014_123456.csv`):

| retailer | run_id | total_attempted | total_success | success_rate_percent | block_rate_percent | proxy_used |
|----------|--------|-----------------|---------------|----------------------|--------------------|------------|
| target   | 1      | 45231           | 45189         | 99.91                | 0.02               | False      |
| costco   | 2      | 12450           | 12398         | 99.58                | 0.15               | False      |

## Troubleshooting

### Issue: "ModuleNotFoundError"

**Solution:**
```bash
# Activate virtual environment first
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Issue: "Playwright browser not found"

**Solution:**
```bash
playwright install chromium
```

### Issue: High block rate (>2%)

**Solutions:**
1. **Add proxy credentials** in `config.py`
2. **Reduce concurrency**:
   ```python
   'concurrency': {
       'target': 10,  # Lower from 25
       'costco': 3,   # Lower from 8
   }
   ```
3. **Increase delays**:
   ```python
   'delays_ms': {'min': 300, 'max': 800}  # More conservative
   ```

### Issue: Cloudflare challenges on Costco

**Solution:**
This should be handled automatically by stealth browser, but if it persists:
1. Enable proxy mode
2. Try from different IP/network
3. Increase delays to 1-2 seconds for Costco specifically

### Issue: Many 404s on HomeGoods/TJ Maxx

**This is normal!** Discount retailers have high inventory churn. 10-20% 404 rate is expected.

### Issue: Out of memory

**Solutions:**
1. **Reduce browser pool**:
   ```python
   'browser_pool_size': 40,  # Lower from 80
   ```
2. **Reduce concurrency**:
   ```python
   'concurrency': {'target': 10, 'costco': 5, ...}
   ```
3. **Run one retailer at a time**:
   ```bash
   python main.py --retailers target
   python main.py --retailers costco
   ```

## Database Queries

The scraper stores data in `scraper_data.db` (SQLite). You can query it directly:

```bash
sqlite3 scraper_data.db
```

### Useful Queries

**Get all Target products:**
```sql
SELECT * FROM products WHERE retailer = 'target';
```

**Count by retailer:**
```sql
SELECT retailer, COUNT(*) FROM products GROUP BY retailer;
```

**Products with no price:**
```sql
SELECT product_id, product_url, title 
FROM products 
WHERE price_current IS NULL;
```

**Error summary:**
```sql
SELECT error_type, COUNT(*) 
FROM errors 
GROUP BY error_type;
```

**Block rate by scrape run:**
```sql
SELECT retailer, block_rate_percent, proxy_used 
FROM scrape_runs 
ORDER BY started_at DESC;
```

## Performance Tuning

### For Speed (if not getting blocked)

```python
'concurrency': {
    'target': 40,
    'costco': 10,
    'homegoods': 30,
    'tjmaxx': 30
},
'delays_ms': {'min': 50, 'max': 200}
```

### For Stealth (if getting blocked)

```python
'concurrency': {
    'target': 10,
    'costco': 3,
    'homegoods': 8,
    'tjmaxx': 8
},
'delays_ms': {'min': 500, 'max': 1500}
```

### For Memory Efficiency

```python
'concurrency': {
    'target': 15,
    'costco': 5,
    'homegoods': 12,
    'tjmaxx': 12
},
'browser_pool_size': 50,
'cleanup_interval_minutes': 10
```

## Next Steps

After successful initial scrape:

1. **Review exports** - Check data quality
2. **Analyze variance** - Ensure completeness
3. **Check errors** - Review failed products
4. **Iterate if needed** - Re-scrape failed items

For delta updates (future):
- Track manifest hash changes
- Re-enumerate for new products
- Compare prices for existing products

