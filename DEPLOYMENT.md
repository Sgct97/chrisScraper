# Deployment Guide

## Running Locally

```bash
# Full scrape (all retailers)
python main.py

# Specific retailers
python main.py --retailers target costco

# Enumeration only (verify counts)
python main.py --enumerate-only

# Resume from previous run
python main.py  # Automatic resume is default

# Fresh start (ignore previous progress)
python main.py --no-resume
```

## Deploying to Render

### Initial Setup

1. **Create GitHub Repository**
```bash
git init
git add .
git commit -m "Initial commit"
git remote add origin <your-github-repo-url>
git push -u origin main
```

2. **Deploy to Render**
   - Go to https://dashboard.render.com
   - Click "New +" > "Blueprint"
   - Connect your GitHub repository
   - Render will detect `render.yaml` and create the worker automatically

3. **Monitor Progress**
   - View logs in Render dashboard
   - Database and exports are persisted on disk
   - Worker will auto-resume if interrupted

### Switching from Render to Local Server

The scraper uses SQLite database with automatic resume:

1. **Download database from Render**
```bash
# Use Render dashboard to download scraper_data.db
# Or use Render CLI: render db download
```

2. **Place database in local directory**
```bash
mv downloaded_scraper_data.db /path/to/chrisScrapper/scraper_data.db
```

3. **Continue scraping locally**
```bash
python main.py  # Will automatically resume from where Render left off
```

## Resource Requirements

### Render (Cloud)
- **Starter Plan**: 0.5 CPU, 512MB RAM - Good for testing
- **Standard Plan**: 1 CPU, 2GB RAM - Recommended for Target
- **Disk**: 10GB persistent storage

### Local Server
- **Minimum**: 4GB RAM, 50GB disk
- **Recommended**: 8GB+ RAM, 100GB+ disk for Target's 2.4M products

## TJ Maxx Residential Proxy Setup

TJ Maxx requires residential proxies due to bot protection:

### Recommended Providers
- **Bright Data**: https://bright data.com (most reliable, $500/month)
- **Smartproxy**: https://smartproxy.com ($75/month, good value)
- **Oxylabs**: https://oxylabs.io ($300/month)

### Configuration

Add to `.env` file:
```bash
RESIDENTIAL_PROXY_URL=http://username:password@proxy-server:port
TJMAXX_PROXY_ENABLED=true
```

Update `config.py`:
```python
CONFIG = {
    'residential_proxy': os.getenv('RESIDENTIAL_PROXY_URL'),
    'tjmaxx_requires_residential': True,
}
```

## Database Location

- **Local**: `./scraper_data.db`
- **Render**: `/opt/render/project/src/scraper_data.db`
- **Exports**: `./exports/` directory

## Monitoring Progress

Check database for progress:
```bash
sqlite3 scraper_data.db "SELECT retailer, COUNT(*) as products FROM products WHERE status='success' GROUP BY retailer;"
```

## Estimated Completion Times

| Retailer | Products | Local (8 cores) | Render (starter) | Render (standard) |
|----------|----------|-----------------|------------------|-------------------|
| Target   | 2.4M     | 3-5 days        | 7-10 days        | 4-6 days          |
| Costco   | 15K      | 2-4 hours       | 4-6 hours        | 2-3 hours         |
| TJ Maxx  | 10K      | 8-12 hours*     | 16-24 hours*     | 10-15 hours*      |

*With residential proxies (very slow due to rate limiting)

