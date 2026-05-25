#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "Installing backend dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python manage.py collectstatic --no-input

echo "Running migrations..."
python manage.py migrate

echo "Seeding database with sample data..."
python manage.py seed_data
