#!/usr/bin/env python
"""
Script to update all templates to use smart_image_url filter
"""

import os
import re

# Templates to update
templates = [
    'orders/templates/orders/menu_list.html',
    'orders/templates/orders/menu_list_dashboard.html', 
    'orders/templates/orders/admin_menu.html',
    'orders/templates/orders/cart.html',
    'orders/templates/orders/cart_dashboard.html',
    'orders/templates/orders/cart_backup.html',
    'orders/templates/orders/menu_item_form.html'
]

for template_path in templates:
    if os.path.exists(template_path):
        print(f"Updating {template_path}")
        
        with open(template_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Add cloudinary_tags loading if not present
        if '{% load cloudinary_tags %}' not in content:
            # Find the first {% extends or {% block and add before it
            if '{% extends' in content:
                content = content.replace('{% extends', '{% load cloudinary_tags %}\n{% extends', 1)
            elif '{% block' in content:
                content = content.replace('{% block', '{% load cloudinary_tags %}\n{% block', 1)
            else:
                content = '{% load cloudinary_tags %}\n' + content
        
        # Replace image.url with smart_image_url filter
        # Pattern: {{ something.image.url }} -> {{ something.image|smart_image_url }}
        content = re.sub(r'\{\{\s*([^}]+\.image)\.url\s*\}\}', r'{{ \1|smart_image_url }}', content)
        
        with open(template_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Updated {template_path}")
    else:
        print(f"❌ Template not found: {template_path}")

print("Template updates completed!")