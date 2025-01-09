#!/usr/bin/env bash
# Exit on error
set -o errexit


STORAGE_DIR=/opt/render/project/.render

if [ ! -d $STORAGE_DIR/chrome ]; then
  echo "...Downloading Chrome"
  mkdir -p $STORAGE_DIR/chrome
  cd $STORAGE_DIR/chrome
  wget -P ./ https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
  dpkg -x ./google-chrome-stable_current_amd64.deb $STORAGE_DIR/chrome
  rm ./google-chrome-stable_current_amd64.deb
  cd $HOME/project/src # Return to the project directory
else
  echo "...Using Chrome from cache"
fi

# Install Python dependencies
pip install -r requirements.txt

# Convert static asset files
python manage.py collectstatic --no-input

# Apply migrations
python manage.py migrate