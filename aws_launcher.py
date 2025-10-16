#!/usr/bin/env python3
"""
AWS Spot Instance Launcher for Target Scraper
Simple script to launch and monitor Spot instances
"""
import boto3
import time
import base64
import sys
from datetime import datetime

# Configuration - UPDATE THESE
CONFIG = {
    'instance_type': 'm6i.2xlarge',  # 32GB RAM, 8 vCPU (better Spot availability)
    'max_price': '0.15',  # Max $/hour for Spot
    'region': 'us-east-1',
    'ami_id': 'ami-0341d95f75f311023',  # Amazon Linux 2023
    'key_name': 'scraper-key',  # Your EC2 key pair name
    'security_group_id': 'sg-06cb555b4b2ec6c99',  # Your security group ID
    'subnet_id': 'subnet-07b5d70ad34e00a01',  # Your subnet ID
    'volume_size_gb': 100,
    'target_concurrency': 50,  # Conservative for 32GB (use 150 with 128GB)
}

# Startup script that runs on the instance
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
export AWS_SPOT_INSTANCE=true
export TARGET_CONCURRENCY={target_concurrency}
export DATABASE_PATH=/data/scraper_data.db
export EXPORT_DIR=/data/exports
export MANIFEST_DIR=/data/manifests

# Start scraper in background with logging
nohup python3.11 main.py --retailers target \
    > /var/log/scraper.log 2>&1 &

echo "=== Scraper started! PID: $! ===" | tee -a /var/log/setup.log
echo "Check progress: tail -f /var/log/scraper.log"
"""


def launch_spot_instance():
    """Launch a Spot instance with the scraper."""
    
    print("=" * 60)
    print("AWS Spot Instance Launcher")
    print("=" * 60)
    print(f"Instance Type: {CONFIG['instance_type']}")
    print(f"Max Price: ${CONFIG['max_price']}/hour")
    print(f"Region: {CONFIG['region']}")
    print(f"Target Concurrency: {CONFIG['target_concurrency']}")
    print("=" * 60)
    print()
    
    # Check for missing config
    if 'xxxxx' in CONFIG['key_name'] or 'xxxxx' in CONFIG['security_group_id']:
        print("ERROR: Please update CONFIG dictionary with your AWS details:")
        print("  - key_name: Your EC2 key pair name")
        print("  - security_group_id: Your security group ID")
        print("  - subnet_id: Your subnet ID")
        print("  - ami_id: AMI ID for your region")
        sys.exit(1)
    
    # Create boto3 client
    ec2 = boto3.client('ec2', region_name=CONFIG['region'])
    
    # Prepare user data script
    user_data = STARTUP_SCRIPT.format(target_concurrency=CONFIG['target_concurrency'])
    user_data_encoded = base64.b64encode(user_data.encode()).decode()
    
    print("Requesting Spot instance...")
    
    try:
        # Request Spot instance
        response = ec2.request_spot_instances(
            SpotPrice=CONFIG['max_price'],
            InstanceCount=1,
            Type='one-time',
            LaunchSpecification={
                'ImageId': CONFIG['ami_id'],
                'InstanceType': CONFIG['instance_type'],
                'KeyName': CONFIG['key_name'],
                'SecurityGroupIds': [CONFIG['security_group_id']],
                'SubnetId': CONFIG['subnet_id'],
                'UserData': user_data_encoded,
                'BlockDeviceMappings': [{
                    'DeviceName': '/dev/xvda',
                    'Ebs': {
                        'VolumeSize': CONFIG['volume_size_gb'],
                        'VolumeType': 'gp3',
                        'DeleteOnTermination': False,  # Persist data on termination
                    }
                }],
            }
        )
        
        request_id = response['SpotInstanceRequests'][0]['SpotInstanceRequestId']
        print(f"✓ Spot request created: {request_id}")
        print("Waiting for fulfillment...")
        
        # Wait for fulfillment
        while True:
            time.sleep(5)
            status = ec2.describe_spot_instance_requests(
                SpotInstanceRequestIds=[request_id]
            )['SpotInstanceRequests'][0]
            
            state = status['State']
            print(f"  Status: {state}")
            
            if state == 'active':
                instance_id = status['InstanceId']
                break
            elif state in ['cancelled', 'failed', 'closed']:
                print(f"ERROR: Request {state}: {status.get('Status', {}).get('Message', 'Unknown')}")
                sys.exit(1)
        
        print(f"✓ Instance launched: {instance_id}")
        print("Waiting for instance to be running...")
        
        # Wait for running
        waiter = ec2.get_waiter('instance_running')
        waiter.wait(InstanceIds=[instance_id])
        
        # Get instance details
        instance = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
        public_ip = instance.get('PublicIpAddress', 'N/A')
        
        print()
        print("=" * 60)
        print("✓ INSTANCE RUNNING!")
        print("=" * 60)
        print(f"Instance ID: {instance_id}")
        print(f"Public IP: {public_ip}")
        print()
        print("Connect:")
        print(f"  ssh -i {CONFIG['key_name']}.pem ec2-user@{public_ip}")
        print()
        print("Monitor scraper:")
        print(f"  ssh ec2-user@{public_ip} 'tail -f /var/log/scraper.log'")
        print()
        print("Check database stats:")
        print(f"  ssh ec2-user@{public_ip} 'cd scraper && python3.11 check_db.py'")
        print()
        print("Download results when done:")
        print(f"  scp -i {CONFIG['key_name']}.pem -r ec2-user@{public_ip}:/data/exports/* ./exports/")
        print(f"  scp -i {CONFIG['key_name']}.pem ec2-user@{public_ip}:/data/scraper_data.db ./")
        print("=" * 60)
        
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)


def check_instance_status(instance_id):
    """Check status of a running instance."""
    ec2 = boto3.client('ec2', region_name=CONFIG['region'])
    
    try:
        instance = ec2.describe_instances(InstanceIds=[instance_id])['Reservations'][0]['Instances'][0]
        
        print(f"Instance: {instance_id}")
        print(f"State: {instance['State']['Name']}")
        print(f"Type: {instance['InstanceType']}")
        print(f"Public IP: {instance.get('PublicIpAddress', 'N/A')}")
        print(f"Launch Time: {instance['LaunchTime']}")
        
    except Exception as e:
        print(f"ERROR: {e}")


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Launch AWS Spot instance for scraping')
    parser.add_argument('--launch', action='store_true', help='Launch new Spot instance')
    parser.add_argument('--status', help='Check status of instance ID')
    parser.add_argument('--concurrency', type=int, help='Override target concurrency (default: 100)')
    
    args = parser.parse_args()
    
    if args.concurrency:
        CONFIG['target_concurrency'] = args.concurrency
    
    if args.launch:
        launch_spot_instance()
    elif args.status:
        check_instance_status(args.status)
    else:
        parser.print_help()

