"""
Export and validation functionality.
"""

import json
from datetime import datetime
from typing import List, Dict
from pathlib import Path
from utils import export_to_json, export_to_csv, export_manifest, ensure_directory, format_timestamp


class Exporter:
    """Handle data export and completeness reporting."""
    
    def __init__(self, config, database):
        self.config = config
        self.database = database
        self.export_dir = ensure_directory(config['export_dir'])
        self.manifests_dir = ensure_directory(config['manifests_dir'])
    
    def export_retailer_data(self, retailer: str):
        """Export all data for a retailer to JSON and CSV."""
        timestamp = format_timestamp()
        
        # Get products from database
        products = self.database.get_products_by_retailer(retailer)
        
        if not products:
            print(f"⚠️  No products found for {retailer}")
            return
        
        # Export JSON
        json_path = self.export_dir / f"export_{retailer}_{timestamp}.json"
        export_to_json(products, str(json_path))
        
        # Export CSV
        csv_path = self.export_dir / f"export_{retailer}_{timestamp}.csv"
        export_to_csv(products, str(csv_path))
        
        print(f"\n✓ Exported {retailer} data:")
        print(f"  - JSON: {json_path}")
        print(f"  - CSV: {csv_path}")
    
    def export_all_retailers(self):
        """Export data for all retailers."""
        retailers = ['target', 'costco', 'homegoods', 'tjmaxx']
        
        for retailer in retailers:
            self.export_retailer_data(retailer)
    
    def generate_completeness_report(self, retailer: str) -> Dict:
        """Generate completeness report for a retailer."""
        counts = self.database.get_enumeration_counts(retailer)
        
        report = {
            'retailer': retailer,
            'timestamp': datetime.now().isoformat(),
            'enumeration_methods': {},
            'variance_analysis': {}
        }
        
        # Group by method
        for count_record in counts:
            method = count_record['method']
            count = count_record['count']
            report['enumeration_methods'][method] = {
                'count': count,
                'timestamp': count_record['timestamp'],
                'notes': count_record['notes']
            }
        
        # Calculate variance between methods
        method_counts = [record['count'] for record in counts]
        if len(method_counts) > 1:
            max_count = max(method_counts)
            min_count = min(method_counts)
            variance_percent = ((max_count - min_count) / max_count * 100) if max_count > 0 else 0
            
            report['variance_analysis'] = {
                'max_count': max_count,
                'min_count': min_count,
                'variance_percent': round(variance_percent, 2),
                'within_threshold': variance_percent <= 2.0  # ±2% threshold
            }
        
        return report
    
    def generate_coverage_report(self, retailer: str, run_id: int) -> Dict:
        """Generate coverage report for a scrape run."""
        stats = self.database.get_scrape_stats(run_id)
        
        if not stats:
            return {}
        
        total = stats['total_attempted']
        success = stats['total_success']
        failed = stats['total_failed']
        
        success_rate = (success / total * 100) if total > 0 else 0
        
        report = {
            'retailer': retailer,
            'run_id': run_id,
            'started_at': stats['started_at'],
            'completed_at': stats['completed_at'],
            'total_attempted': total,
            'total_success': success,
            'total_failed': failed,
            'success_rate_percent': round(success_rate, 2),
            'block_rate_percent': stats['block_rate_percent'],
            'proxy_used': bool(stats['proxy_used']),
            'meets_target': success_rate >= 98.0  # ≥98% target
        }
        
        return report
    
    def export_completeness_package(self):
        """Export complete proof of completeness package."""
        timestamp = format_timestamp()
        
        retailers = ['target', 'costco', 'homegoods', 'tjmaxx']
        
        completeness_reports = {}
        for retailer in retailers:
            report = self.generate_completeness_report(retailer)
            if report:
                completeness_reports[retailer] = report
        
        # Export completeness report
        completeness_path = self.export_dir / f"completeness_report_{timestamp}.json"
        export_to_json(completeness_reports, str(completeness_path))
        
        # Generate variance analysis text
        variance_path = self.export_dir / f"variance_analysis_{timestamp}.txt"
        with open(variance_path, 'w') as f:
            f.write("VARIANCE ANALYSIS - Multi-Method Enumeration\n")
            f.write("=" * 80 + "\n\n")
            
            for retailer, report in completeness_reports.items():
                f.write(f"{retailer.upper()}\n")
                f.write("-" * 40 + "\n")
                
                for method, data in report.get('enumeration_methods', {}).items():
                    f.write(f"  {method}: {data['count']:,} products\n")
                
                variance = report.get('variance_analysis', {})
                if variance:
                    f.write(f"\n  Variance: {variance.get('variance_percent', 0):.2f}%\n")
                    f.write(f"  Within ±2% threshold: {variance.get('within_threshold', False)}\n")
                
                f.write("\n\n")
        
        print(f"\n✓ Completeness package exported:")
        print(f"  - {completeness_path}")
        print(f"  - {variance_path}")
    
    def export_coverage_matrix(self, retailer_runs: Dict[str, int]):
        """Export coverage matrix for all retailers."""
        timestamp = format_timestamp()
        
        coverage_data = []
        for retailer, run_id in retailer_runs.items():
            report = self.generate_coverage_report(retailer, run_id)
            if report:
                coverage_data.append(report)
        
        # Export as CSV
        csv_path = self.export_dir / f"coverage_matrix_{timestamp}.csv"
        export_to_csv(coverage_data, str(csv_path))
        
        print(f"✓ Coverage matrix exported: {csv_path}")
    
    def print_summary(self, retailer_runs: Dict[str, int]):
        """Print summary statistics."""
        print("\n" + "=" * 80)
        print("SCRAPE SUMMARY")
        print("=" * 80 + "\n")
        
        for retailer, run_id in retailer_runs.items():
            report = self.generate_coverage_report(retailer, run_id)
            if report:
                print(f"{retailer.upper()}")
                print(f"  Attempted: {report['total_attempted']:,}")
                print(f"  Success: {report['total_success']:,} ({report['success_rate_percent']:.2f}%)")
                print(f"  Failed: {report['total_failed']:,}")
                print(f"  Block Rate: {report['block_rate_percent']:.2f}%")
                print(f"  Proxy Used: {'Yes' if report['proxy_used'] else 'No'}")
                print(f"  Meets Target (≥98%): {'✓' if report['meets_target'] else '✗'}")
                print()

