from django.contrib import admin

from .models import MenuCategory, MenuItem


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
  list_display = ("name", "is_featured")
  list_filter = ("is_featured",)
  prepopulated_fields = {"slug": ("name",)}


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
  list_display = ("name", "category", "price", "is_available", "tag")
  list_filter = ("category", "is_available", "tag")
  search_fields = ("name", "description")
  list_editable = ("price", "is_available", "tag")
