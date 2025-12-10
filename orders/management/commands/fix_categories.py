from django.core.management.base import BaseCommand
from orders.models import MenuCategory


class Command(BaseCommand):
    help = 'Fix category issues by removing Popular/New categories and ensuring standard ones exist'

    def handle(self, *args, **options):
        self.stdout.write("Fixing categories...")
        
        # Delete Popular and New categories
        deleted_count, _ = MenuCategory.objects.filter(name__in=['Popular', 'New']).delete()
        self.stdout.write("✓ Deleted {} invalid categories (Popular/New)".format(deleted_count))
        
        # Ensure standard categories exist
        standard_categories = [
            'Breakfast',
            'Lunch', 
            'Snack',
            'Beverage',
        ]
        
        created_count = 0
        for cat_name in standard_categories:
            category, created = MenuCategory.objects.get_or_create(name=cat_name)
            if created:
                created_count += 1
                self.stdout.write("✓ Created category: {}".format(cat_name))
        
        if created_count == 0:
            self.stdout.write("✓ All standard categories already exist")
        
        # Show final categories
        all_categories = MenuCategory.objects.all()
        self.stdout.write("\nFinal categories ({}):".format(all_categories.count()))
        for cat in all_categories:
            self.stdout.write("  - {}".format(cat.name))
        
        self.stdout.write(self.style.SUCCESS("\n✅ Categories fixed successfully!"))