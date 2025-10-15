"""
Database schema and operations for SQLite storage.
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import contextmanager


class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize database with schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Products table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS products (
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
                    specifications TEXT,  -- JSON string
                    image_urls TEXT,  -- JSON string (array)
                    ratings_average REAL,
                    ratings_count INTEGER,
                    shipping_cost REAL,
                    shipping_estimate TEXT,
                    variants TEXT,  -- JSON string
                    seller TEXT,
                    scraped_at TIMESTAMP,
                    scrape_run_id INTEGER,
                    status TEXT DEFAULT 'success'
                )
            """)
            
            # Scrape runs table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS scrape_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    retailer TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    total_attempted INTEGER DEFAULT 0,
                    total_success INTEGER DEFAULT 0,
                    total_failed INTEGER DEFAULT 0,
                    block_rate_percent REAL DEFAULT 0.0,
                    proxy_used BOOLEAN DEFAULT 0
                )
            """)
            
            # Enumeration counts table (for proof of completeness)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enumeration_counts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    retailer TEXT,
                    method TEXT,
                    count INTEGER,
                    timestamp TIMESTAMP,
                    notes TEXT
                )
            """)
            
            # Errors table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS errors (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    retailer TEXT,
                    product_url TEXT,
                    error_type TEXT,
                    error_message TEXT,
                    html_snapshot TEXT,
                    timestamp TIMESTAMP,
                    scrape_run_id INTEGER
                )
            """)
            
            conn.commit()
    
    @contextmanager
    def get_connection(self):
        """Context manager for database connections."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def create_scrape_run(self, retailer: str, proxy_used: bool = False) -> int:
        """Create a new scrape run and return its ID."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO scrape_runs (retailer, started_at, proxy_used)
                VALUES (?, ?, ?)
            """, (retailer, datetime.now(), proxy_used))
            conn.commit()
            return cursor.lastrowid
    
    def update_scrape_run(self, run_id: int, **kwargs):
        """Update scrape run with stats."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
            query = f"UPDATE scrape_runs SET {set_clause} WHERE id = ?"
            cursor.execute(query, list(kwargs.values()) + [run_id])
            conn.commit()
    
    def insert_product(self, product_data: Dict[str, Any]):
        """Insert or update a product record."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Convert complex types to JSON strings
            if 'specifications' in product_data and isinstance(product_data['specifications'], (dict, list)):
                product_data['specifications'] = json.dumps(product_data['specifications'])
            if 'image_urls' in product_data and isinstance(product_data['image_urls'], list):
                product_data['image_urls'] = json.dumps(product_data['image_urls'])
            if 'variants' in product_data and isinstance(product_data['variants'], (dict, list)):
                product_data['variants'] = json.dumps(product_data['variants'])
            
            # Set scraped_at if not present
            if 'scraped_at' not in product_data:
                product_data['scraped_at'] = datetime.now()
            
            columns = ', '.join(product_data.keys())
            placeholders = ', '.join(['?' for _ in product_data])
            
            cursor.execute(f"""
                INSERT OR REPLACE INTO products ({columns})
                VALUES ({placeholders})
            """, list(product_data.values()))
            conn.commit()
    
    def insert_enumeration_count(self, retailer: str, method: str, count: int, notes: str = None):
        """Record enumeration count for proof of completeness."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO enumeration_counts (retailer, method, count, timestamp, notes)
                VALUES (?, ?, ?, ?, ?)
            """, (retailer, method, count, datetime.now(), notes))
            conn.commit()
    
    def log_error(self, retailer: str, product_url: str, error_type: str, 
                  error_message: str, scrape_run_id: int, html_snapshot: str = None):
        """Log an error that occurred during scraping."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO errors (retailer, product_url, error_type, error_message, 
                                    html_snapshot, timestamp, scrape_run_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (retailer, product_url, error_type, error_message, 
                  html_snapshot, datetime.now(), scrape_run_id))
            conn.commit()
    
    def get_products_by_retailer(self, retailer: str) -> List[Dict]:
        """Get all products for a retailer."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE retailer = ?", (retailer,))
            rows = cursor.fetchall()
            
            products = []
            for row in rows:
                product = dict(row)
                # Parse JSON fields
                if product.get('specifications'):
                    try:
                        product['specifications'] = json.loads(product['specifications'])
                    except:
                        pass
                if product.get('image_urls'):
                    try:
                        product['image_urls'] = json.loads(product['image_urls'])
                    except:
                        pass
                if product.get('variants'):
                    try:
                        product['variants'] = json.loads(product['variants'])
                    except:
                        pass
                products.append(product)
            
            return products
    
    def get_enumeration_counts(self, retailer: str) -> List[Dict]:
        """Get enumeration counts for a retailer."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT method, count, timestamp, notes 
                FROM enumeration_counts 
                WHERE retailer = ?
                ORDER BY timestamp DESC
            """, (retailer,))
            return [dict(row) for row in cursor.fetchall()]
    
    def get_scrape_stats(self, run_id: int) -> Dict:
        """Get statistics for a scrape run."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM scrape_runs WHERE id = ?", (run_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

