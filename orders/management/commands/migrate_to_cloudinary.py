import os
from django.core.management.base import BaseCommand
from django.conf import settings
from orders.models import MenuItem
import cloudinary.uploader


class Command(BaseCommand):
    help = 'Migrate existing local images to Cloudinary'

    def handle(self, *args, **options):
        if not all([
            settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'),
            settings.CLOUDINARY_STORAGE.get('API_KEY'),
            settings.CLOUDINARY_STORAGE.get('API_SECRET')
        ]):
            self.stdout.write(
                self.style.ERROR('Cloudinary credentials not configured. Please set environment variables.')
            )
            return

        migrated_count = 0
        failed_count = 0

        for item in MenuItem.objects.all():
            if item.image and hasattr(item.image, 'path'):
                try:
                    # Check if file exists locally
                    if os.path.exists(item.image.path):
                        self.stdout.write(f'Migrating image for: {item.name}')
                        
                        # Upload to Cloudinary
                        result = cloudinary.uploader.upload(
                            item.image.path,
                            folder='menu_items',
                            public_id=f'menu_item_{item.id}_{item.name.lower().replace(" ", "_")}',
                            overwrite=True
                        )
                        
                        # Update the model with Cloudinary URL
                        item.image = result['public_id']
                        item.save()
                        
                        migrated_count += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'✓ Migrated: {item.name}')
                        )
                    else:
                        self.stdout.write(
                            self.style.WARNING(f'Local file not found for: {item.name}')
                        )
                        
                except Exception as e:
                    failed_count += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Failed to migrate {item.name}: {str(e)}')
                    )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nMigration complete! Migrated: {migrated_count}, Failed: {failed_count}'
            )
        )