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
python manage.py shell << EOF
from orders.models import MenuCategory

categories = [
    {'name': 'Breakfast', 'description': 'Start your day with our delicious breakfast options'},
    {'name': 'Lunch', 'description': 'Hearty lunch meals to keep you energized'},
    {'name': 'Dinner', 'description': 'Satisfying dinner dishes for a perfect evening'},
    {'name': 'Beverages', 'description': 'Refreshing drinks and beverages'},
    {'name': 'Desserts', 'description': 'Sweet treats to end your meal'},
]

for cat_data in categories:
    category, created = MenuCategory.objects.get_or_create(
        name=cat_data['name'],
        defaults={'description': cat_data['description']}
    )
    if created:
        print(f'Created category: {cat_data[\"name\"]}')
    else:
        print(f'Category already exists: {cat_data[\"name\"]}')
EOF