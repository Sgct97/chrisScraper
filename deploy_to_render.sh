#!/bin/bash
# Deploy scraper to Render
# Usage: ./deploy_to_render.sh

echo "Preparing for Render deployment..."

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Render deployment"
fi

echo ""
echo "Next steps:"
echo "1. Create a new GitHub repository (public or private)"
echo "2. Push this code: git remote add origin <your-repo-url> && git push -u origin main"
echo "3. Go to https://dashboard.render.com"
echo "4. Click 'New +' > 'Blueprint'"
echo "5. Connect your GitHub repo"
echo "6. Render will automatically detect render.yaml and create the worker"
echo ""
echo "The scraper will start automatically and resume if interrupted."
echo "You can monitor logs in the Render dashboard."

