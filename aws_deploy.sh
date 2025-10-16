#!/bin/bash
# AWS Spot Instance Deployment Script
# Launches a Spot instance and deploys the scraper

set -e  # Exit on error

# Configuration
INSTANCE_TYPE="${INSTANCE_TYPE:-r6i.4xlarge}"  # 128GB RAM, 16 vCPU
AMI_ID="${AMI_ID:-ami-0c55b159cbfafe1f0}"  # Amazon Linux 2023 (update for your region)
SECURITY_GROUP="${SECURITY_GROUP:-sg-xxxxx}"  # Replace with your security group
KEY_NAME="${KEY_NAME:-your-key-name}"  # Replace with your EC2 key pair name
SUBNET_ID="${SUBNET_ID:-subnet-xxxxx}"  # Replace with your subnet
SPOT_PRICE="${SPOT_PRICE:-0.30}"  # Max price per hour (r6i.4xlarge spot ~$0.20-0.30)
REGION="${AWS_REGION:-us-east-1}"

# Target concurrency (100 for 128GB instance, adjust based on RAM)
TARGET_CONCURRENCY="${TARGET_CONCURRENCY:-100}"

echo "=========================================="
echo "AWS Spot Instance Deployment"
echo "=========================================="
echo "Instance Type: $INSTANCE_TYPE"
echo "Region: $REGION"
echo "Max Spot Price: \$$SPOT_PRICE/hour"
echo "Target Concurrency: $TARGET_CONCURRENCY"
echo "=========================================="
echo

# Create user data script for instance initialization
cat > /tmp/user_data.sh << 'USERDATA'
#!/bin/bash
# Auto-setup script for Spot instance

set -e

# Update system
yum update -y

# Install dependencies
yum install -y git python3.11 python3.11-pip docker

# Install Docker and start service
systemctl start docker
systemctl enable docker

# Clone repository
cd /home/ec2-user
git clone https://github.com/Sgct97/chrisScraper.git scraper
cd scraper

# Switch to main branch with all fixes
git checkout main
git pull

# Install Python dependencies
python3.11 -m pip install --upgrade pip
python3.11 -m pip install -r requirements.txt

# Install Playwright browsers
python3.11 -m playwright install chromium
python3.11 -m playwright install-deps

# Set environment variables
export AWS_SPOT_INSTANCE=true
export TARGET_CONCURRENCY=${TARGET_CONCURRENCY}
export DATABASE_PATH=/data/scraper_data.db
export EXPORT_DIR=/data/exports
export MANIFEST_DIR=/data/manifests

# Create data directory (persists on EBS volume)
mkdir -p /data/exports /data/manifests

# Set ownership
chown -R ec2-user:ec2-user /home/ec2-user/scraper
chown -R ec2-user:ec2-user /data

# Create systemd service for auto-restart on interruption
cat > /etc/systemd/system/scraper.service << 'SERVICE'
[Unit]
Description=Target Product Scraper
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/scraper
Environment="AWS_SPOT_INSTANCE=true"
Environment="TARGET_CONCURRENCY=${TARGET_CONCURRENCY}"
Environment="DATABASE_PATH=/data/scraper_data.db"
Environment="EXPORT_DIR=/data/exports"
Environment="MANIFEST_DIR=/data/manifests"
ExecStart=/usr/bin/python3.11 /home/ec2-user/scraper/main.py --retailers target
Restart=on-failure
RestartSec=10
StandardOutput=append:/var/log/scraper.log
StandardError=append:/var/log/scraper_error.log

[Install]
WantedBy=multi-user.target
SERVICE

# Enable and start service
systemctl daemon-reload
systemctl enable scraper
systemctl start scraper

echo "Scraper deployment complete! Check status with: systemctl status scraper"
echo "Logs: tail -f /var/log/scraper.log"
USERDATA

echo "Creating Spot instance request..."
echo

# Request Spot instance
INSTANCE_ID=$(aws ec2 request-spot-instances \
    --region $REGION \
    --spot-price "$SPOT_PRICE" \
    --instance-count 1 \
    --type "one-time" \
    --launch-specification "{
        \"ImageId\": \"$AMI_ID\",
        \"InstanceType\": \"$INSTANCE_TYPE\",
        \"KeyName\": \"$KEY_NAME\",
        \"SecurityGroupIds\": [\"$SECURITY_GROUP\"],
        \"SubnetId\": \"$SUBNET_ID\",
        \"UserData\": \"$(base64 -w0 /tmp/user_data.sh)\",
        \"BlockDeviceMappings\": [{
            \"DeviceName\": \"/dev/xvda\",
            \"Ebs\": {
                \"VolumeSize\": 100,
                \"VolumeType\": \"gp3\",
                \"DeleteOnTermination\": false
            }
        }],
        \"IamInstanceProfile\": {
            \"Name\": \"EC2SpotInstanceProfile\"
        }
    }" \
    --query 'SpotInstanceRequests[0].SpotInstanceRequestId' \
    --output text)

echo "✓ Spot instance request created: $INSTANCE_ID"
echo
echo "Waiting for instance to start..."
aws ec2 wait spot-instance-request-fulfilled --region $REGION --spot-instance-request-ids $INSTANCE_ID

# Get instance ID
INSTANCE=$(aws ec2 describe-spot-instance-requests \
    --region $REGION \
    --spot-instance-request-ids $INSTANCE_ID \
    --query 'SpotInstanceRequests[0].InstanceId' \
    --output text)

echo "✓ Instance started: $INSTANCE"

# Get public IP
PUBLIC_IP=$(aws ec2 describe-instances \
    --region $REGION \
    --instance-ids $INSTANCE \
    --query 'Reservations[0].Instances[0].PublicIpAddress' \
    --output text)

echo
echo "=========================================="
echo "✓ DEPLOYMENT SUCCESSFUL!"
echo "=========================================="
echo "Instance ID: $INSTANCE"
echo "Public IP: $PUBLIC_IP"
echo
echo "Connect with:"
echo "  ssh -i $KEY_NAME.pem ec2-user@$PUBLIC_IP"
echo
echo "Monitor scraper:"
echo "  ssh ec2-user@$PUBLIC_IP 'tail -f /var/log/scraper.log'"
echo
echo "Check status:"
echo "  ssh ec2-user@$PUBLIC_IP 'systemctl status scraper'"
echo
echo "Download results:"
echo "  scp -i $KEY_NAME.pem ec2-user@$PUBLIC_IP:/data/exports/* ./exports/"
echo "=========================================="

# Clean up
rm -f /tmp/user_data.sh

