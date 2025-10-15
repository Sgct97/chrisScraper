"""
Utility functions for scraping, exports, and helpers.
"""

import json
import csv
import hashlib
from datetime import datetime
from typing import List, Dict, Any
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_exponential
import asyncio


def calculate_sha256(data: str) -> str:
    """Calculate SHA-256 hash of string data."""
    return hashlib.sha256(data.encode()).hexdigest()


def ensure_directory(path: str) -> Path:
    """Ensure directory exists, create if needed."""
    directory = Path(path)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def export_to_json(data: List[Dict], filepath: str):
    """Export data to JSON file."""
    ensure_directory(Path(filepath).parent)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)
    print(f"✓ Exported {len(data)} items to {filepath}")


def export_to_csv(data: List[Dict], filepath: str):
    """Export data to CSV file."""
    if not data:
        print(f"⚠️  No data to export to {filepath}")
        return
    
    ensure_directory(Path(filepath).parent)
    
    # Get all unique keys from all records
    all_keys = set()
    for record in data:
        all_keys.update(record.keys())
    
    fieldnames = sorted(all_keys)
    
    with open(filepath, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for record in data:
            # Convert lists/dicts to JSON strings for CSV
            row = {}
            for key, value in record.items():
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                else:
                    row[key] = value
            writer.writerow(row)
    
    print(f"✓ Exported {len(data)} items to {filepath}")


def export_manifest(urls: List[str], filepath: str) -> str:
    """Export manifest of URLs with SHA-256 hash."""
    ensure_directory(Path(filepath).parent)
    
    # Sort URLs for consistent hashing
    sorted_urls = sorted(set(urls))
    
    # Write manifest
    with open(filepath, 'w', encoding='utf-8') as f:
        for url in sorted_urls:
            f.write(f"{url}\n")
    
    # Calculate hash
    manifest_data = '\n'.join(sorted_urls)
    manifest_hash = calculate_sha256(manifest_data)
    
    # Write hash file
    hash_filepath = filepath.replace('.csv', '.sha256')
    with open(hash_filepath, 'w') as f:
        f.write(manifest_hash)
    
    print(f"✓ Exported manifest: {len(sorted_urls)} URLs, hash: {manifest_hash[:16]}...")
    return manifest_hash


def format_timestamp() -> str:
    """Get formatted timestamp for filenames."""
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def retry_with_backoff(max_attempts: int = 3):
    """Decorator for retry logic with exponential backoff."""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True
    )


class ProgressTracker:
    """Track and display scraping progress."""
    
    def __init__(self, total: int, retailer: str):
        self.total = total
        self.retailer = retailer
        self.success = 0
        self.failed = 0
        self.blocked = 0
        self.not_found = 0
        self.start_time = datetime.now()
        
    def record_success(self):
        self.success += 1
        
    def record_failure(self, error_type: str = 'failed'):
        if error_type == 'blocked':
            self.blocked += 1
        elif error_type == 'not_found':
            self.not_found += 1
        else:
            self.failed += 1
    
    def get_stats(self) -> Dict:
        """Get current statistics."""
        completed = self.success + self.failed + self.blocked + self.not_found
        elapsed = (datetime.now() - self.start_time).total_seconds()
        items_per_min = (completed / elapsed * 60) if elapsed > 0 else 0
        block_rate = (self.blocked / completed * 100) if completed > 0 else 0
        
        return {
            'completed': completed,
            'total': self.total,
            'success': self.success,
            'failed': self.failed,
            'blocked': self.blocked,
            'not_found': self.not_found,
            'items_per_min': round(items_per_min, 1),
            'block_rate_percent': round(block_rate, 2),
            'elapsed_seconds': round(elapsed, 1)
        }
    
    def print_progress(self, mode: str = "Home Network"):
        """Print progress bar and stats."""
        stats = self.get_stats()
        completed = stats['completed']
        total = stats['total']
        percent = (completed / total * 100) if total > 0 else 0
        
        # Progress bar
        bar_length = 40
        filled = int(bar_length * completed / total) if total > 0 else 0
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r[{mode}] {bar} {percent:.1f}% | "
              f"Success: {stats['success']:,} | Failed: {stats['failed']} | "
              f"Blocked: {stats['blocked']} | Block Rate: {stats['block_rate_percent']}% | "
              f"Speed: {stats['items_per_min']:.1f} items/min", 
              end='', flush=True)


async def gather_with_concurrency(n: int, *tasks):
    """Run async tasks with limited concurrency."""
    semaphore = asyncio.Semaphore(n)
    
    async def sem_task(task):
        async with semaphore:
            return await task
    
    return await asyncio.gather(*(sem_task(task) for task in tasks))

