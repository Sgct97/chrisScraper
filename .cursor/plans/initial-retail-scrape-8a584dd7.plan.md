<!-- 8a584dd7-5f1b-4059-abfe-842badbaba96 9a2024b7-bc3e-4437-9194-920678f87673 -->
# Initial Retail Scrape - Production Architecture

## Architecture Overview

Build modular scraper with:

- **Playwright + stealth** for browser automation (playwright-stealth, undetected-chromedriver compatible)
- **Async/await** for concurrency (optimized for 32GB RAM)
- **API interception** where possible (Target GraphQL, etc.)
- **SQLite** for storage with JSON/CSV export
- **Image URL extraction only** (no downloads, just capture URLs)
- **Multi-method enumeration** for proof of completeness
- **Home network first** - proxies ONLY when blocked
- **Per-retailer modules** - each site needs unique scraper (different APIs, structures, protections)

## Phase 1: Infrastructure Setup

### Core Components

- `config.py`: Settings (ZIP code, delays, concurrency, proxy credentials, user agents)
- `database.py`: SQLite schema with tables: `products`, `scrape_runs`, `errors`, `enumeration_counts`
- `proxy_manager.py`: Rotating proxy pool with health checks, **disabled by default**, auto-enable on blocks
- `browser_manager.py`: Playwright context factory with stealth patches (playwright-stealth), cookie persistence
- `rate_limiter.py`: Per-domain rate limiting with jitter (150-500ms for home IP)
- `utils.py`: Retry decorators, hashing, export functions (JSON/CSV)

### Dependencies

```
playwright>=1.40
playwright-stealth>=0.1.6  # Stealth patches for anti-detection
httpx>=0.25
beautifulsoup4>=4.12
tenacity>=8.2
fake-useragent>=1.4
```

## Phase 2: Proof of Completeness System

**CRITICAL**: Multi-source enumeration to prove we captured everything.

### Verification Strategy Per Retailer

**Target**:

1. **Sitemap enumeration**: Parse `sitemap_products.xml` index, count all product URLs
2. **API category counts**: Query GraphQL for category totals, aggregate
3. **Search validation**: Use site search API with broad queries, check "X total results"
4. Deliverable: `target_completeness.json` with counts from all 3 methods + variance %

**Costco** (public data only, no membership):

1. **Sitemap enumeration**: Full sitemap parse + count
2. **Category crawl**: Paginate all departments, count unique item numbers
3. **Search check**: Broad search queries to verify total product count
4. **Note**: Flag items with "member price" hidden - capture what's public
5. Deliverable: `costco_completeness.json` with method comparison

**HomeGoods & TJ Maxx** (no comprehensive sitemaps):

1. **Full category tree**: Crawl all categories with pagination, count unique SKUs
2. **Cross-validation**: Multiple entry points (Shop by Category, New Arrivals, All Products)
3. **Stability check**: Re-enumerate after 3 hours, expect <5% variance (normal inventory churn)
4. Deliverable: Per-site completeness files with category-level counts

### Completeness Proof Package

- `completeness_report.json`: All enumeration counts per site, per method
- `variance_analysis.txt`: Explain discrepancies between enumeration methods
- `coverage_matrix.csv`: Attempted/succeeded/failed/blocked breakdown
- `manifest_master.csv`: Final deduped list with SHA-256 hash for verification

### Success Criteria

- Multiple enumeration methods agree within ±2%
- Successfully scraped ≥98% of enumerated items
- All failures categorized (404, blocked, gated, parsing error)

## Phase 3: Per-Retailer Scrapers

**Each retailer gets its own scraper** - cannot share due to different structures:

### Target Scraper (`scrapers/target.py`)

**Strategy**: Intercept GraphQL API

1. **Enumeration**: Sitemap + GraphQL category API
2. **Scraping**: Intercept `pdp_client_v1` GraphQL calls for clean JSON
3. **Fallback**: Parse `__NEXT_DATA__` script tag if API fails
4. **Fields**: TCIN, title, price, brand, specs, **image_urls** (array of URLs), shipping (best effort), ratings

### Costco Scraper (`scrapers/costco.py`)

**Strategy**: Stealth browser with Cloudflare bypass

1. **Enumeration**: Sitemap + category pagination
2. **Public only**: No login, flag "member price" items as `price_unavailable`
3. **Anti-block**: Conservative rate (500ms+), max 8 concurrent browsers
4. **Fields**: Item number, title, price (when visible), **image_urls**, department

### HomeGoods Scraper (`scrapers/homegoods.py`)

**Strategy**: Category pagination

1. **Enumeration**: Full category tree crawl (no reliable sitemap)
2. **Scraping**: Parse product cards from listing pages, then visit PDPs
3. **Fields**: SKU, title, price, category, **image_urls**, availability

### TJ Maxx Scraper (`scrapers/tjmaxx.py`)

**Strategy**: Similar to HomeGoods (same parent company TJX)

1. **Enumeration**: Category-based enumeration
2. **Scraping**: Product listing extraction + PDP visits
3. **Expected churn**: High 404 rate normal for discount retailer
4. **Fields**: SKU, title, price, category, **image_urls**, availability

## Phase 4: Orchestration

### Main Workflow (`main.py`)

1. **Initialize**: DB setup, proxy health check (test if credentials provided, keep disabled)
2. **Multi-Source Enumeration**: 

   - Run sitemap parsers
   - Run category crawlers  
   - Run search validators
   - Cross-check counts, generate completeness report

3. **Dedupe & Merge**: Combine all sources, dedupe by URL/ID, create master manifest
4. **PDP Scraping**: Multi-async workers:

   - Fetch product page (browser or API)
   - Extract all fields including image URLs
   - Write product data to DB with status

5. **Real-time Monitoring**: 

   - Success rate, block rate, items/min
   - Auto-switch to proxies if block rate exceeds threshold

6. **Validation**: Check coverage, required fields
7. **Export**: Generate JSON/CSV files
8. **Final Report**: Completeness proof + coverage stats

### Error Handling

- **Block detection**: Auto-switch to proxies if block rate >2% in 5min window OR 10+ consecutive failures
- **CAPTCHA**: Pause, log alert, attempt proxy rotation
- **404s**: Expected for inventory sites, log and continue
- **Parsing errors**: Log HTML snapshot, mark as failed, continue

## Phase 5: Data Schema

### Products Table

```sql
CREATE TABLE products (
    product_id TEXT PRIMARY KEY,
    retailer TEXT NOT NULL,
    product_url TEXT NOT NULL,
    title TEXT,
    brand TEXT,
    category TEXT,
    price_current REAL,
    price_compare_at REAL,
    currency TEXT DEFAULT 'USD',
    availability TEXT,
    description TEXT,
    specifications JSON,
    image_urls JSON,  -- Array of image URLs (no local downloads)
    ratings_average REAL,
    ratings_count INTEGER,
    shipping_cost REAL,       -- Best effort
    shipping_estimate TEXT,   -- Best effort
    variants JSON,
    seller TEXT,
    scraped_at TIMESTAMP,
    scrape_run_id INTEGER
);
```

### Enumeration Counts Table (for proof)

```sql
CREATE TABLE enumeration_counts (
    id INTEGER PRIMARY KEY,
    retailer TEXT,
    method TEXT, -- 'sitemap', 'category_crawl', 'search_api'
    count INTEGER,
    timestamp TIMESTAMP,
    notes TEXT
);
```

### Scrape Runs Table

```sql
CREATE TABLE scrape_runs (
    id INTEGER PRIMARY KEY,
    retailer TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    total_attempted INTEGER,
    total_success INTEGER,
    total_failed INTEGER,
    block_rate_percent REAL,
    proxy_used BOOLEAN
);
```

## Phase 6: Validation & Export

### Quality Checks

- ≥98% of manifest attempted
- Required fields: product_id, url, title, price (or `price_unavailable` flag)
- Image URLs: Verify array format, valid URLs
- Completeness: All enumeration methods reconciled

### Export Files

- `export_{site}_{timestamp}.json`: Full product data with image URL arrays
- `export_{site}_{timestamp}.csv`: Flattened CSV (image_urls as JSON string or pipe-separated)
- `completeness_report.json`: Multi-method enumeration proof
- `coverage_matrix.csv`: Success/failure breakdown
- `manifest_master.csv`: All product URLs with SHA-256 hash

## Configuration - Optimized for Local 32GB Machine

**Default Mode**: Run on **home network**, auto-escalate to proxies ONLY when blocked.

```python
CONFIG = {
    'zip_code': '90210',  # Set your ZIP for location-based pricing
    
    # Concurrency optimized for 32GB RAM (each Playwright instance ~150-200MB)
    # Can run ~80-100 browser instances comfortably
    'concurrency': {
        'target': 25,      # Moderate - API calls are fast
        'costco': 8,       # Conservative - Cloudflare + anti-bot
        'homegoods': 20,   # Lighter protection
        'tjmaxx': 20       # Lighter protection
    },
    
    'delays_ms': {'min': 150, 'max': 500},  # Home IP needs conservative delays
    
    # Proxy settings - DISABLED by default, only enable when blocked
    'proxy': {
        'enabled': False,  # Start on HOME NETWORK
        'auto_enable_on_blocks': True,  # Auto-switch when threshold hit
        'datacenter_pool': None,  # Set "http://user:pass@proxy:port" if you have credentials
        'switch_threshold_percent': 2.0,  # Switch if >2% blocks in 5min
        'switch_threshold_count': 10  # Or 10+ consecutive failures
    },
    
    'retries': 3,
    'timeout_seconds': 30,
    
    # Memory management for 32GB machine
    'max_memory_percent': 75,  # Use max 75% of RAM (~24GB)
    'browser_pool_size': 80,   # Max concurrent browser instances
    'cleanup_interval_minutes': 15  # Restart contexts to prevent memory leaks
}
```

### Proxy Escalation Logic

**Stay on home IP unless:**

1. Block rate >2% over 5-minute rolling window, OR
2. 10+ consecutive 403/429/CAPTCHA errors, OR
3. Manual override flag set

**When switching to proxies:**

- Log alert: "PROXY ESCALATION: [reason] at [timestamp]"
- Pause scraping for 60 seconds
- Test proxy with 5 sample requests
- Resume with proxies enabled
- Continue monitoring (can switch back if blocks drop below 0.5%)

**Live Dashboard (terminal output):**

```
[Home Network Mode] | Success: 1,234 | Failed: 12 | Block Rate: 0.8% | Speed: 45 items/min
```

## Testing Strategy

1. **Enumeration test**: Run all 3 methods for Target, verify ±2% agreement
2. **Smoke test**: 10 products per site, verify field extraction + image URLs
3. **Proxy test**: If credentials provided, test 5 requests to confirm working
4. **Rate test**: 100 products at target concurrency, measure block rate on home IP
5. **Export test**: Validate JSON/CSV schemas, verify image URLs are valid

## Milestones

**M1 (Infrastructure + Enumeration)**: Build core + implement multi-source enumeration for Target → Prove completeness methodology works

**M2 (All Retailers)**: Complete all 4 scrapers + full enumeration → Generate completeness reports showing total item counts

**M3 (Full Scrape)**: Execute initial scrape on home network → Deliver JSON/CSV exports + completeness proof package

## Critical Decisions

1. **Different scraper per site**: Cannot reuse - each has unique API/structure/protection
2. **Multi-source enumeration**: Only way to prove completeness without insider data
3. **Image URLs only**: No downloads, just capture URL arrays (simpler, faster)
4. **Home IP first**: Start on home network, auto-escalate to proxies only when blocked
5. **32GB RAM optimized**: Can run ~80 concurrent browsers, aggressive parallelization
6. **Costco public only**: No membership login, flag member-only prices
7. **Shipping best effort**: Capture if visible on PDP without checkout

## What's INCLUDED

- ✅ Image URL extraction (no downloads)
- ✅ Multi-method enumeration for completeness proof
- ✅ Per-retailer custom scrapers (Target, Costco, HomeGoods, TJ Maxx)
- ✅ Home network first with auto-proxy escalation
- ✅ JSON/CSV export for initial scrape
- ✅ Optimized for 32GB RAM machine
- ✅ Comprehensive validation and coverage reporting

## What's SKIPPED

- ❌ Image downloading (URLs only)
- ❌ Delta updates (future phase)
- ❌ Price change monitoring
- ❌ Scheduling/cron jobs
- ❌ Costco membership login
- ❌ Complex shipping extraction requiring checkout

### To-dos

- [ ] Build core infrastructure: config, database schema, proxy manager, browser manager with stealth, rate limiter
- [ ] Implement Target scraper with GraphQL interception and sitemap enumeration
- [ ] Implement Costco scraper with Cloudflare bypass and public-data-only extraction
- [ ] Implement HomeGoods and TJ Maxx scrapers (shared TJX approach)
- [ ] Build main orchestrator: enumeration, queue management, multi-async workers, monitoring dashboard
- [ ] Implement validation checks and export to JSON/CSV with coverage reporting
- [ ] Run 10-item smoke test per site, verify extraction quality and block rate
- [ ] Execute full initial scrape, monitor for blocks, generate final exports and coverage report