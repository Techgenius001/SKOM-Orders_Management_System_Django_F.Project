#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
pip install -r requirements-prod.txt

python manage.py collectstatic --no-input
python manage.py migrate

# Create superuser automatically if it doesn't exist
python manage.py shell << EOF
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'samuelnjhihia333@gmail.com', 'Admin@2024')
    print('Superuser created successfully')
else:
    print('Superuser already exists')
EOF

# Create default menu categories
python manage.py create_categories

# Migrate existing images to Cloudinary (only if Cloudinary is configured)
python manage.py migrate_images_to_cloudinary --force