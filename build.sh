#!/usr/bin/env bash
# Exit on error
set -o errexit

# Create local bin directory if it doesn't exist
mkdir -p ~/bin

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

# Install ChromeDriver to user's bin directory
unzip ~/chromedriver_linux64.zip -d ~/
rm ~/chromedriver_linux64.zip
chmod 0755 ~/chromedriver
mv -f ~/chromedriver ~/bin/chromedriver

# Add local bin to PATH
export PATH=$PATH:~/bin

# Install Python dependencies
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply migrations
python manage.py migrate