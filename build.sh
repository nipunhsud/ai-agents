#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install Chrome and Xvfb
apt-get update && apt-get install -y \
    google-chrome-stable \
    xvfb \
    x11-utils \
    unzip \
    wget

# Set up virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x16 &

# Install ChromeDriver
CHROME_DRIVER_VERSION=`curl -sS https://chromedriver.storage.googleapis.com/LATEST_RELEASE`
wget -N https://chromedriver.storage.googleapis.com/$CHROME_DRIVER_VERSION/chromedriver_linux64.zip -P ~/
unzip ~/chromedriver_linux64.zip -d ~/
rm ~/chromedriver_linux64.zip
mv -f ~/chromedriver /usr/local/bin/chromedriver
chmod 0755 /usr/local/bin/chromedriver

# Install Python dependencies
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply migrations
python manage.py migrate