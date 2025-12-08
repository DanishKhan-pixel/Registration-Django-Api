#!/bin/bash

echo "Running pre-deployment commands..."

python manage.py migrate
python manage.py sync_permissions
python manage.py sync_roles
python manage.py mysuperuser
python manage.py collectstatic --noinput  # Optional, if needed

echo "All commands executed successfully!"



# lsof -i :8001 -P -n

# To kill the process on that port:

# lsof -ti :8001 -sTCP:LISTEN | xargs kill -9