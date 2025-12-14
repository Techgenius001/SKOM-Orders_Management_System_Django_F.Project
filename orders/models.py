from django.conf import settings
from django.db import models
from django.utils.text import slugify
from django.core.mail import send_mail
from django.template.loader import render_to_string



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
    is_featured = models.BooleanField(default=False, help_text="Show on homepage")
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



class Order(models.Model):
    """Customer order with delivery and payment details."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        PREPARING = 'preparing', 'Preparing'
        OUT_FOR_DELIVERY = 'out_for_delivery', 'Out for Delivery'
        DELIVERED = 'delivered', 'Delivered'
        CANCELLED = 'cancelled', 'Cancelled'

    class PaymentMethod(models.TextChoices):
        CASH = 'cash', 'Cash on Delivery'
        MPESA = 'mpesa', 'M-Pesa'

    order_number = models.CharField(max_length=20, unique=True, editable=False, blank=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    delivery_location = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    notes = models.TextField(blank=True, default='')
    
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"Order {self.order_number} - {self.user.username}"

    def save(self, *args, **kwargs):
        if not self.order_number or self.order_number == 'ORD-00000000-0000':
            # Generate order number: ORD-YYYYMMDD-XXXX
            from django.utils import timezone
            import random
            
            date_str = timezone.now().strftime('%Y%m%d')
            
            # Try to find the last order for today
            last_order = Order.objects.filter(
                order_number__startswith=f'ORD-{date_str}'
            ).order_by('-order_number').first()
            
            if last_order:
                try:
                    last_num = int(last_order.order_number.split('-')[-1])
                    new_num = last_num + 1
                except (ValueError, IndexError):
                    new_num = random.randint(1000, 9999)
            else:
                new_num = 1
            
            # Generate unique order number
            max_attempts = 10
            for _ in range(max_attempts):
                self.order_number = f'ORD-{date_str}-{new_num:04d}'
                if not Order.objects.filter(order_number=self.order_number).exists():
                    break
                new_num += 1
        
        super().save(*args, **kwargs)


class OrderItem(models.Model):
    """Individual item in an order."""

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=8, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.quantity}x {self.menu_item.name}"

    def get_total_price(self):
        """Calculate total price for this order item."""
        return self.price * self.quantity



class ContactInquiry(models.Model):
    """Customer inquiry submitted through contact form."""
    
    class Status(models.TextChoices):
        NEW = 'new', 'New'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
    
    class SubjectType(models.TextChoices):
        ORDER_INQUIRY = 'order_inquiry', 'Order Inquiry'
        GENERAL_QUESTION = 'general_question', 'General Question'
        FEEDBACK = 'feedback', 'Feedback'
        COMPLAINT = 'complaint', 'Complaint'
        OTHER = 'other', 'Other'
    
    # Customer Information
    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    
    # Inquiry Details
    subject_type = models.CharField(max_length=20, choices=SubjectType.choices)
    order_number = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    
    # Status Tracking
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.NEW)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Contact Inquiries'
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['status']),
            models.Index(fields=['email']),
            models.Index(fields=['name']),
        ]
    
    def __str__(self) -> str:
        return f"{self.name} - {self.get_subject_type_display()}"
