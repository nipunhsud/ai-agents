#!/usr/bin/env bash
# Exit on error
set -o errexit


# Set up virtual display
export DISPLAY=:99
Xvfb :99 -screen 0 1024x768x16 &

# Install ChromeDriver to user's bin directory
unzip ~/chromedriver_linux64.zip -d ~/
rm ~/chromedriver_linux64.zip
chmod 0755 ~/chromedriver
mv -f ~/chromedriver ~/bin/chromedriver


# Install Python dependencies
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply migrations
python manage.py migrate