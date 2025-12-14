"""
Template tags for Cloudinary image handling.
"""

from django import template
from django.conf import settings
import os

register = template.Library()


@register.filter
def cloudinary_url(image_field, transformation=None):
    """
    Generate Cloudinary URL for an image field.
    Usage: {{ menu_item.image|cloudinary_url:"w_300,h_200,c_fill" }}
    """
    if not image_field:
        return ''
    
    # In production with Cloudinary
    if os.environ.get('RENDER') and hasattr(settings, 'CLOUDINARY_STORAGE'):
        try:
            # If it's already a Cloudinary URL, return as is
            if 'cloudinary.com' in str(image_field.url):
                if transformation:
                    # Insert transformation into existing URL
                    url_parts = str(image_field.url).split('/upload/')
                    if len(url_parts) == 2:
                        return f"{url_parts[0]}/upload/{transformation}/{url_parts[1]}"
                return str(image_field.url)
        except:
            pass
    
    # Fallback to regular URL
    try:
        return image_field.url
    except:
        return ''


@register.simple_tag
def cloudinary_thumbnail(image_field, width=300, height=200):
    """
    Generate a thumbnail URL for Cloudinary images.
    Usage: {% cloudinary_thumbnail menu_item.image 300 200 %}
    """
    transformation = f"w_{width},h_{height},c_fill,q_auto,f_auto"
    return cloudinary_url(image_field, transformation)