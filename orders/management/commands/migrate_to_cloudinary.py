import os
from django.core.management.base import BaseCommand
from django.conf import settings
from orders.models import MenuItem
import cloudinary.uploader


class Command(BaseCommand):
    help = 'Migrate existing local images to Cloudinary'

    def handle(self, *args, **options):
        # Check if Cloudinary is configured
        if not all([
            settings.CLOUDINARY_STORAGE.get('CLOUD_NAME'),
            settings.CLOUDINARY_STORAGE.get('API_KEY'),
            settings.CLOUDINARY_STORAGE.get('API_SECRET')
        ]):
            self.stdout.write(
                self.style.WARNING('Cloudinary credentials not configured. Skipping migration.')
            )
            return

        self.stdout.write('Starting Cloudinary migration...')
        migrated_count = 0
        failed_count = 0

        # Sample images mapping for production (since local files don't exist in production)
        sample_images = {
            'Fresh Passion Juice': 'https://images.unsplash.com/photo-1622597467836-f3285f2131b8?auto=format&fit=crop&w=500&q=80',
            'Chips Masala': 'https://images.unsplash.com/photo-1585032226651-759b368d7246?auto=format&fit=crop&w=500&q=80',
            'Fish Fry': 'https://images.unsplash.com/photo-1544943910-4c1dc44aab44?auto=format&fit=crop&w=500&q=80',
            'Beef Stew': 'https://images.unsplash.com/photo-1574484284002-952d92456975?auto=format&fit=crop&w=500&q=80',
            'Mango Smoothie': 'https://images.unsplash.com/photo-1553530666-ba11a7da3888?auto=format&fit=crop&w=500&q=80',
            'Mbuzi Choma': 'https://images.unsplash.com/photo-1529692236671-f1f6cf9683ba?auto=format&fit=crop&w=500&q=80',
            'Pilau': 'https://images.unsplash.com/photo-1596797038530-2c107229654b?auto=format&fit=crop&w=500&q=80',
            'Sausages': 'https://images.unsplash.com/photo-1529042410759-befb1204b468?auto=format&fit=crop&w=500&q=80',
            'Githeri': 'https://images.unsplash.com/photo-1574484284002-952d92456975?auto=format&fit=crop&w=500&q=80',
            'Chapati': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?auto=format&fit=crop&w=500&q=80',
            'Tea': 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=500&q=80',
            'Coffee': 'https://images.unsplash.com/photo-1495474472287-4d71bcdd2085?auto=format&fit=crop&w=500&q=80',
        }

        for item in MenuItem.objects.all():
            try:
                # Find a suitable image URL
                image_url = None
                for key, url in sample_images.items():
                    if key.lower() in item.name.lower():
                        image_url = url
                        break
                
                if not image_url:
                    # Default food image
                    image_url = 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?auto=format&fit=crop&w=500&q=80'

                self.stdout.write(f'Migrating image for: {item.name}')
                
                # Upload to Cloudinary from URL
                result = cloudinary.uploader.upload(
                    image_url,
                    folder='menu_items',
                    public_id=f'menu_item_{item.id}_{item.name.lower().replace(" ", "_").replace("(", "").replace(")", "")}',
                    overwrite=True
                )
                
                # Update the model with Cloudinary public_id
                item.image = result['public_id']
                item.save()
                
                migrated_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Migrated: {item.name} -> {result["secure_url"]}')
                )
                        
            except Exception as e:
                failed_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Failed to migrate {item.name}: {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'\nCloudinary migration complete! Migrated: {migrated_count}, Failed: {failed_count}'
            )
        )