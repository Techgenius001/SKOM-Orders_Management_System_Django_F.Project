#!/usr/bin/env python
"""
Debug script to check image URLs and storage configuration
Run this in production to see what's happening with images
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartkibadaski.settings')
django.setup()

from orders.models import MenuItem

print("=== IMAGE DEBUG INFO ===")
print(f"RENDER environment: {os.environ.get('RENDER')}")
print(f"DEBUG: {settings.DEBUG}")
print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")
print(f"MEDIA_URL: {settings.MEDIA_URL}")
print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")

print("\n=== CLOUDINARY CONFIG ===")
cloudinary_storage = getattr(settings, 'CLOUDINARY_STORAGE', {})
print(f"CLOUD_NAME: {cloudinary_storage.get('CLOUD_NAME', 'Not set')}")
print(f"API_KEY: {cloudinary_storage.get('API_KEY', 'Not set')}")
print(f"API_SECRET: {'***' if cloudinary_storage.get('API_SECRET') else 'Not set'}")

print("\n=== MENU ITEMS WITH IMAGES ===")
items_with_images = MenuItem.objects.filter(image__isnull=False).exclude(image='')

if not items_with_images.exists():
    print("No menu items with images found")
else:
    for item in items_with_images:
        print(f"\nItem: {item.name}")
        print(f"Image field: {item.image}")
        print(f"Image name: {item.image.name if item.image else 'None'}")
        try:
            print(f"Image URL: {item.image.url}")
        except Exception as e:
            print(f"Error getting URL: {e}")
        
        # Check if file exists locally
        if item.image:
            local_path = os.path.join(settings.MEDIA_ROOT, item.image.name)
            print(f"Local file exists: {os.path.exists(local_path)}")