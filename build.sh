#!/usr/bin/env bash
# Exit on error
set -o errexit

STORAGE_DIR=/opt/render/project/.render

# Install Chrome and its dependencies
echo "Installing Chrome and dependencies..."
apt-get update
apt-get install -y wget gnupg2
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google.list
apt-get update
apt-get install -y google-chrome-stable

# Set Chrome binary path
export CHROME_BIN=/usr/bin/google-chrome-stable

# Install Python dependencies
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply migrations
python manage.py migrate