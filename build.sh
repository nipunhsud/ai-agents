#!/bin/bash

# Create postgres role if it doesn't exist
psql postgres -c "CREATE ROLE postgres WITH LOGIN SUPERUSER PASSWORD 'postgres'" || true

# Create database if it doesn't exist
psql postgres -c "CREATE DATABASE ai_assistant OWNER postgres" || true

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input

