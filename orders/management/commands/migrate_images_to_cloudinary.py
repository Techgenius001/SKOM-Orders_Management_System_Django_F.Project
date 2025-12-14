"""
Management command to migrate existing local images to Cloudinary.
Run this after deploying to production to ensure all images are uploaded to Cloudinary.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.files.base import ContentFile
from orders.models import MenuItem
import os
import requests


class Command(BaseCommand):
    help = 'Migrate existing local images to Cloudinary storage'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even in development',
        )

    def handle(self, *args, **options):
        if not options['force'] and not os.environ.get('RENDER'):
            self.stdout.write(
                self.style.WARNING('This command should only be run in production. Use --force to override.')
            )
            return

        # Check if Cloudinary is configured
        cloudinary_storage = getattr(settings, 'CLOUDINARY_STORAGE', {})
        if not all([
            cloudinary_storage.get('CLOUD_NAME'),
            cloudinary_storage.get('API_KEY'),
            cloudinary_storage.get('API_SECRET')
        ]):
            self.stdout.write(
                self.style.ERROR('Cloudinary credentials not configured')
            )
            return

        self.stdout.write('=== DEBUG INFO ===')
        self.stdout.write(f'DEFAULT_FILE_STORAGE: {getattr(settings, "DEFAULT_FILE_STORAGE", "Not set")}')
        self.stdout.write(f'MEDIA_URL: {settings.MEDIA_URL}')
        self.stdout.write(f'Cloudinary Cloud Name: {cloudinary_storage.get("CLOUD_NAME")}')

        menu_items = MenuItem.objects.filter(image__isnull=False).exclude(image='')
        
        if not menu_items.exists():
            self.stdout.write(
                self.style.SUCCESS('No menu items with images found')
            )
            return

        self.stdout.write(f'Found {menu_items.count()} menu items with images')
        
        for item in menu_items:
            try:
                if item.image:
                    self.stdout.write(f'\nProcessing: {item.name}')
                    self.stdout.write(f'Current image: {item.image.name}')
                    
                    try:
                        current_url = item.image.url
                        self.stdout.write(f'Current URL: {current_url}')
                        
                        # Check if it's already a Cloudinary URL
                        if 'cloudinary.com' in current_url:
                            self.stdout.write(
                                self.style.SUCCESS(f'Already on Cloudinary: {item.name}')
                            )
                            continue
                            
                    except Exception as e:
                        self.stdout.write(f'Error getting URL: {e}')
                    
                    # Try to re-save to trigger Cloudinary upload
                    item.save()
                    
                    # Check new URL
                    try:
                        new_url = item.image.url
                        self.stdout.write(f'New URL: {new_url}')
                        if 'cloudinary.com' in new_url:
                            self.stdout.write(
                                self.style.SUCCESS(f'Successfully migrated: {item.name}')
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'Still not on Cloudinary: {item.name}')
                            )
                    except Exception as e:
                        self.stdout.write(f'Error getting new URL: {e}')
                        
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to migrate {item.name}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS('Image migration completed')
        )