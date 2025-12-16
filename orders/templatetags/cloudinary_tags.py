"""
Template tags for Cloudinary image handling.
"""

from django import template
from django.conf import settings
import os

register = template.Library()


@register.filter
def smart_image_url(image_field):
    """
    Smart image URL that handles both uploaded files and external URLs.
    Usage: {{ menu_item.image|smart_image_url }}
    """
    if not image_field:
        return ''
    
    try:
        # Get the image name/path
        image_name = str(image_field.name) if hasattr(image_field, 'name') else str(image_field)
        
        # If it's an external URL (starts with http), return as is
        if image_name.startswith('http'):
            return image_name
            
        # If it's a local file, use the normal URL method
        return image_field.url
        
    except Exception as e:
        # Fallback: if it looks like a URL, return it
        image_str = str(image_field)
        if image_str.startswith('http'):
            return image_str
        return ''


@register.filter
def cloudinary_url(image_field, transformation=None):
    """
    Generate Cloudinary URL for an image field.
    Usage: {{ menu_item.image|cloudinary_url:"w_300,h_200,c_fill" }}
    """
    if not image_field:
        return ''
    
    # First get the smart URL
    base_url = smart_image_url(image_field)
    
    # If it's an external URL, return as is (no Cloudinary processing)
    if base_url.startswith('http') and 'cloudinary.com' not in base_url:
        return base_url
    
    # In production with Cloudinary
    if os.environ.get('RENDER') and hasattr(settings, 'CLOUDINARY_STORAGE'):
        try:
            # If it's already a Cloudinary URL, return as is
            if 'cloudinary.com' in base_url:
                if transformation:
                    # Insert transformation into existing URL
                    url_parts = base_url.split('/upload/')
                    if len(url_parts) == 2:
                        return f"{url_parts[0]}/upload/{transformation}/{url_parts[1]}"
                return base_url
        except:
            pass
    
    return base_url


@register.simple_tag
def cloudinary_thumbnail(image_field, width=300, height=200):
    """
    Generate a thumbnail URL for Cloudinary images.
    Usage: {% cloudinary_thumbnail menu_item.image 300 200 %}
    """
    transformation = f"w_{width},h_{height},c_fill,q_auto,f_auto"
    return cloudinary_url(image_field, transformation)