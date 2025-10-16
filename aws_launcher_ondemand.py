#!/usr/bin/env python3
"""
AWS On-Demand Instance Launcher (instant, no waiting for Spot)
"""
import boto3
import time
import base64
import sys
from datetime import datetime

# Configuration
CONFIG = {
    'instance_type': 'm6i.2xlarge',  # 32GB RAM, 8 vCPU
    'region': 'us-east-1',
    'ami_id': 'ami-0341d95f75f311023',  # Amazon Linux 2023
    'key_name': 'scraper-key',
    'security_group_id': 'sg-06cb555b4b2ec6c99',
    'subnet_id': 'subnet-07b5d70ad34e00a01',
    'volume_size_gb': 100,
    'target_concurrency': 50,
}

# Startup script
STARTUP_SCRIPT = """#!/bin/bash
set -e

echo "=== Starting scraper setup at $(date) ===" | tee -a /var/log/setup.log

# Update and install dependencies
sudo yum update -y
sudo yum install -y git python3.11 python3.11-pip

# Clone repo
cd /home/ec2-user
if [ ! -d "scraper" ]; then
    git clone https://github.com/Sgct97/chrisScraper.git scraper
fi

cd scraper
git checkout main
git pull

# Install Python deps
python3.11 -m pip install --upgrade pip
python3.11 -m pip install -r requirements.txt
python3.11 -m playwright install chromium
sudo python3.11 -m playwright install-deps

# Create data directory
sudo mkdir -p /data/exports /data/manifests
sudo chown -R ec2-user:ec2-user /data

# Set environment
export AWS_SPOT_INSTANCE=false
export TARGET_CONCURRENCY={target_concurrency}
export DATABASE_PATH=/data/scraper_data.db
export EXPORT_DIR=/data/exports
export MANIFEST_DIR=/data/manifests

# Start scraper in background with logging
nohup python3.11 main.py --retailers target > /var/log/scraper.log 2>&1 &

echo "=== Scraper started! PID: $! ===" | tee -a /var/log/setup.log
"""

def launch_ondemand_instance():
    """Launch an On-Demand instance."""
    
    print("=" * 60)
    print("AWS On-Demand Instance Launcher")
    print("=" * 60)
    print(f"Instance Type: {CONFIG['instance_type']}")
    print(f"Cost: ~$0.38/hour")
    print(f"Region: {CONFIG['region']}")
    print(f"Target Concurrency: {CONFIG['target_concurrency']}")
    print("=" * 60)
    print()
    
    ec2 = boto3.client('ec2', region_name=CONFIG['region'])
    
    user_data = STARTUP_SCRIPT.format(target_concurrency=CONFIG['target_concurrency'])
    
    print("Launching On-Demand instance...")
    
    try:
        response = ec2.run_instances(
            ImageId=CONFIG['ami_id'],
            InstanceType=CONFIG['instance_type'],
            KeyName=CONFIG['key_name'],
            SecurityGroupIds=[CONFIG['security_group_id']],
            # Don't specify SubnetId - let AWS pick available AZ
            UserData=user_data,
            MinCount=1,
            MaxCount=1,
            BlockDeviceMappings=[{
                'DeviceName': '/dev/xvda',
                'Ebs': {
                    'VolumeSize': CONFIG['volume_size_gb'],
                    'VolumeType': 'gp3',
                    'DeleteOnTermination': False,
                }
            }],
        )
        
        instance_id = response['Instances'][0]['InstanceId']
        print(f"✓ Instance launched: {instance_id}")
        print("Waiting for instance to be running...")
        
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        instance = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
        public_ip = instance.get('PublicIpAddress', 'N/A')
        
        print()
        print("=" * 60)
        print("✓ INSTANCE RUNNING!")
        print("=" * 60)
        print(f"Instance ID: {instance_id}")
        print(f"Public IP: {public_ip}")
        print(f"Cost: ~$0.38/hour (~$9/day)")
        print()
        print("Setup will take 5-10 minutes, then scraping starts.")
        print()
        print("Monitor:")
        print(f"  python3 monitor_scraper.py {public_ip} --key scraper-key.pem --live")
        print()
        print("SSH:")
        print(f"  ssh -i scraper-key.pem ec2-user@{public_ip}")
        print()
        print("Terminate when done:")
        print(f"  aws ec2 terminate-instances --instance-ids {instance_id}")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)

if __name__ == '__main__':
    launch_ondemand_instance()

