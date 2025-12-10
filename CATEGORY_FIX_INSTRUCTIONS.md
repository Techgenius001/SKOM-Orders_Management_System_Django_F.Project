# Category Fix Instructions for Production

## Problem Fixed

- Categories dropdown in admin menu form was showing "--------" (no categories)
- Menu page was only showing "All Items", "Popular", and "New" filters (missing actual category filters like Breakfast, Lunch, etc.)

## Root Cause

The database had "Popular" and "New" as MenuCategory objects when they should only exist as MenuItem tags. The code was excluding these, which worked locally but caused issues in production.

## Changes Made

1. **orders/views.py**: Removed the `exclude(name__in=['Popular', 'New'])` logic from HomeView and MenuListView
2. **fix_categories.py**: Created script to clean up invalid categories and ensure standard categories exist

## Deployment Steps

### After Render Redeploys:

1. **SSH into your Render instance** or use Render Shell

2. **Run the fix script**:

   ```bash
   python fix_categories.py
   ```

3. **Verify categories exist**:

   ```bash
   python manage.py shell -c "from orders.models import MenuCategory; print([c.name for c in MenuCategory.objects.all()])"
   ```

   Expected output: `['Beverage', 'Breakfast', 'Lunch', 'Snack']`

4. **Check the admin form** - Categories should now appear in the dropdown

5. **Check the menu page** - Should show category filter buttons: All Items, Beverage, Breakfast, Lunch, Snack, Popular, New

## What the Fix Does

The `fix_categories.py` script:

- Deletes any "Popular" or "New" categories (they should only be tags)
- Creates standard categories if missing: Breakfast, Lunch, Snack, Beverage
- Shows final category list

## Verification

After deployment, verify:

1. ✅ Admin menu form shows all 4 categories in dropdown
2. ✅ Menu page shows 4 category filters + 2 tag filters (Popular/New)
3. ✅ Clicking each filter works correctly
4. ✅ Menu items display under correct categories
