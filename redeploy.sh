#!/bin/bash

# Pull the latest code from the staging branch
echo "🔄 Pulling latest code from staging..."
git pull origin staging

# Activate the virtual environment
echo "🐍 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📦 Installing dependencies..."
pip3 install -r requirements.txt

# Apply database migrations
echo "📂 Applying migrations..."
python3 manage.py migrate --noinput

# Collect static files
echo "🗂️ Collecting static files..."
python3 manage.py collectstatic --noinput

# Sync Permissions
echo "🗂️ Sync Permissions..."
python3 manage.py sync_permissions

# Sync Roles
echo "🗂️ Sync Roles..."
python3 manage.py sync_roles

# Creating or Updating Super User
echo "🗂️ Creating or Updating Super User..."
python3 manage.py mysuperuser

# Restart Gunicorn and Nginx
echo "🚀 Restarting services..."
sudo systemctl daemon-reexec
sudo systemctl restart gunicorn
sudo systemctl restart nginx

echo "✅ Redeploy complete."
