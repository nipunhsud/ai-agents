#!/usr/bin/env bash
# Exit on error
set -o errexit

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

STORAGE_DIR=/opt/render/project/.render

# Create Chrome directory
mkdir -p $STORAGE_DIR/chrome
cd $STORAGE_DIR/chrome

# Download Chrome binary
echo "Downloading Chrome..."
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
dpkg -x google-chrome-stable_current_amd64.deb .
rm google-chrome-stable_current_amd64.deb

# Set Chrome binary path
export CHROME_BIN=$STORAGE_DIR/chrome/opt/google/chrome/google-chrome

# Return to project directory
cd "$SCRIPT_DIR"

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply migrations
python manage.py migrate