"""
Management command to migrate existing local images to Cloudinary.
Run this after deploying to production to ensure all images are uploaded to Cloudinary.
"""

from django.core.management.base import BaseCommand
from django.conf import settings
from orders.models import MenuItem
import os


class Command(BaseCommand):
    help = 'Migrate existing local images to Cloudinary storage'

    def handle(self, *args, **options):
        if not os.environ.get('RENDER'):
            self.stdout.write(
                self.style.WARNING('This command should only be run in production')
            )
            return

        # Check if Cloudinary is configured
        if not all([
            settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'),
            settings.CLOUDINARY_STORAGE.get('API_KEY'),
            settings.CLOUDINARY_STORAGE.get('API_SECRET')
        ]):
            self.stdout.write(
                self.style.ERROR('Cloudinary credentials not configured')
            )
            return

        menu_items = MenuItem.objects.filter(image__isnull=False)
        
        if not menu_items.exists():
            self.stdout.write(
                self.style.SUCCESS('No menu items with images found')
            )
            return

        self.stdout.write(f'Found {menu_items.count()} menu items with images')
        
        for item in menu_items:
            try:
                if item.image:
                    # Re-save the item to trigger Cloudinary upload
                    old_image = item.image
                    item.save()
                    self.stdout.write(
                        self.style.SUCCESS(f'Migrated image for: {item.name}')
                    )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Failed to migrate {item.name}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS('Image migration completed')
        )