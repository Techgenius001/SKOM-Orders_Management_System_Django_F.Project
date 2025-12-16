#!/usr/bin/env python
"""
Simple test to verify Cloudinary is working
Run this in production to test actual upload
"""

import os
import django
from django.conf import settings

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'smartkibadaski.settings')
django.setup()

print("=== CLOUDINARY TEST ===")
print(f"DEFAULT_FILE_STORAGE: {getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set')}")

# Test if we can import cloudinary
try:
    import cloudinary
    import cloudinary.uploader
    print("✅ Cloudinary imported successfully")
    
    # Test upload
    result = cloudinary.uploader.upload(
        "https://via.placeholder.com/300x200/FF0000/FFFFFF?text=TEST",
        folder="menu_items",
        public_id="test_upload"
    )
    print(f"✅ Test upload successful: {result['secure_url']}")
    
except Exception as e:
    print(f"❌ Cloudinary error: {e}")

print("=== END TEST ===")