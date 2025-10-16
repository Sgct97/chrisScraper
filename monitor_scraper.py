#!/usr/bin/env python3
"""
Monitor scraper progress remotely via SSH
"""
import sys
import time
import paramiko
from datetime import datetime


def monitor_scraper(host, key_file, username='ec2-user'):
    """Connect and monitor scraper progress in real-time."""
    
    print(f"Connecting to {host}...")
    
    try:
        # Setup SSH client
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, key_filename=key_file)
        
        print(f"✓ Connected to {host}\n")
        print("=" * 80)
        print("SCRAPER PROGRESS MONITOR")
        print("=" * 80)
        print()
        
        # Get database stats
        print("Fetching current stats...\n")
        stdin, stdout, stderr = ssh.exec_command('cd scraper && python3.11 check_db.py')
        output = stdout.read().decode()
        print(output)
        
        print("\n" + "=" * 80)
        print("LIVE LOG (Ctrl+C to exit)")
        print("=" * 80 + "\n")
        
        # Tail the log file
        stdin, stdout, stderr = ssh.exec_command('tail -f /var/log/scraper.log')
        
        try:
            for line in iter(stdout.readline, ""):
                print(line, end='')
                sys.stdout.flush()
        except KeyboardInterrupt:
            print("\n\nMonitoring stopped.")
        
        ssh.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def get_quick_stats(host, key_file, username='ec2-user'):
    """Get quick stats without live monitoring."""
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, key_filename=key_file)
        
        # Get stats
        stdin, stdout, stderr = ssh.exec_command('cd scraper && python3.11 check_db.py')
        stats = stdout.read().decode()
        
        # Get last 20 log lines
        stdin, stdout, stderr = ssh.exec_command('tail -20 /var/log/scraper.log')
        logs = stdout.read().decode()
        
        ssh.close()
        
        print("=" * 80)
        print(f"Quick Stats - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        print(stats)
        print("\n" + "=" * 80)
        print("Recent Activity")
        print("=" * 80)
        print(logs)
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def download_results(host, key_file, username='ec2-user'):
    """Download database and exports."""
    
    print(f"Downloading results from {host}...")
    
    try:
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh.connect(host, username=username, key_filename=key_file)
        
        sftp = ssh.open_sftp()
        
        # Download database
        print("Downloading database...")
        sftp.get('/data/scraper_data.db', './scraper_data_aws.db')
        print("✓ Database downloaded: ./scraper_data_aws.db")
        
        # List exports
        try:
            exports = sftp.listdir('/data/exports')
            print(f"\nFound {len(exports)} export files")
            
            for export_file in exports:
                local_path = f'./exports/{export_file}'
                remote_path = f'/data/exports/{export_file}'
                print(f"Downloading {export_file}...")
                sftp.get(remote_path, local_path)
            
            print(f"\n✓ All exports downloaded to ./exports/")
        except:
            print("No exports found yet")
        
        sftp.close()
        ssh.close()
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor scraper on AWS instance')
    parser.add_argument('host', help='Instance public IP address')
    parser.add_argument('--key', required=True, help='Path to SSH key file (.pem)')
    parser.add_argument('--live', action='store_true', help='Live log monitoring')
    parser.add_argument('--download', action='store_true', help='Download results')
    
    args = parser.parse_args()
    
    if args.download:
        download_results(args.host, args.key)
    elif args.live:
        monitor_scraper(args.host, args.key)
    else:
        get_quick_stats(args.host, args.key)

