"""
Add this to your urls.py temporarily to debug image issues
"""

from django.http import JsonResponse
from django.conf import settings
from orders.models import MenuItem
import os

def debug_images(request):
    """Debug view to check image configuration"""
    
    debug_info = {
        'environment': {
            'RENDER': os.environ.get('RENDER'),
            'DEBUG': settings.DEBUG,
            'DEFAULT_FILE_STORAGE': getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set'),
            'MEDIA_URL': settings.MEDIA_URL,
            'MEDIA_ROOT': str(settings.MEDIA_ROOT),
        },
        'cloudinary': {
            'CLOUD_NAME': getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME', 'Not set'),
            'API_KEY': getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_KEY', 'Not set'),
            'API_SECRET_SET': bool(getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_SECRET')),
        },
        'menu_items': []
    }
    
    # Get menu items with images
    items_with_images = MenuItem.objects.filter(image__isnull=False).exclude(image='')[:5]  # Limit to 5
    
    for item in items_with_images:
        item_info = {
            'name': item.name,
            'image_name': item.image.name if item.image else None,
        }
        
        try:
            item_info['image_url'] = item.image.url
        except Exception as e:
            item_info['image_url_error'] = str(e)
            
        debug_info['menu_items'].append(item_info)
    
    return JsonResponse(debug_info, indent=2)