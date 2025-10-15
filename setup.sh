#!/bin/bash

# Setup script for retail scraper

echo "Setting up Retail Product Scraper..."
echo

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install Playwright browsers
echo "Installing Playwright browsers..."
playwright install chromium

# Create directories
echo "Creating output directories..."
mkdir -p exports
mkdir -p manifests

echo
echo "✓ Setup complete!"
echo
echo "To run the scraper:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Configure settings in config.py (ZIP code, proxy if needed)"
echo "  3. Run: python main.py"
echo
echo "For test mode: python main.py --test"
echo

