#!/usr/bin/env python
"""
Fix a single template file
"""

template_path = 'orders/templates/orders/menu_item_form.html'

with open(template_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add cloudinary_tags load after humanize
content = content.replace(
    '{% load humanize %}',
    '{% load humanize %}\n{% load cloudinary_tags %}'
)

# Replace image.url with smart_image_url filter
content = content.replace(
    'src="{{menu_item.image.url}}"',
    'src="{{menu_item.image|smart_image_url}}"'
)

with open(template_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("Template fixed successfully!")