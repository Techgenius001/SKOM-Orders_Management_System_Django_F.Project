from django.db import models
from django.utils.text import slugify


class MenuCategory(models.Model):
    """High-level grouping for menu items (Breakfast, Lunch, etc.)."""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    is_featured = models.BooleanField(default=False)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class MenuItem(models.Model):
    """Single dish that can be ordered from the hotel menu."""

    class Tags(models.TextChoices):
        NONE = "none", "None"
        POPULAR = "popular", "Popular"
        NEW = "new", "New"

    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    category = models.ForeignKey(
        MenuCategory, related_name="items", on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to="menu_items/", blank=True, null=True)
    is_available = models.BooleanField(default=True)
    tag = models.CharField(
        max_length=20,
        choices=Tags.choices,
        default=Tags.NONE,
        help_text="Used for badges like Popular / New.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
