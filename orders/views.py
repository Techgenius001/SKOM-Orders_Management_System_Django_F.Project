from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView

from .cart import Cart
from .models import MenuCategory, MenuItem, Order, OrderItem


class HomeView(TemplateView):
    """Landing page where customers will browse a preview of the menu."""

    template_name = 'orders/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        categories = MenuCategory.objects.all()
        
        # Get filter parameters
        selected_category = self.request.GET.get("category") or ""
        selected_tag = self.request.GET.get("tag") or ""
        
        # Filter items based on selection
        items = MenuItem.objects.filter(is_available=True)
        if selected_category:
            items = items.filter(category__slug=selected_category)
        elif selected_tag in ['popular', 'new']:
            items = items.filter(tag=selected_tag)
        else:
            # Show featured items on homepage when no filter is selected
            items = items.filter(is_featured=True)
        
        items = items[:8]

        context["categories"] = categories
        context["menu_items"] = items
        context["selected_category"] = selected_category
        context["selected_tag"] = selected_tag
        return context


class MenuListView(ListView):
    """Full menu page with filters by category/tag."""

    model = MenuItem
    context_object_name = 'menu_items'

    def get_template_names(self):
        """Use dashboard layout if user is logged in."""
        if self.request.user.is_authenticated:
            return ['orders/menu_list_dashboard.html']
        return ['orders/menu_list.html']

    def get_queryset(self):
        qs = MenuItem.objects.filter(is_available=True)
        self.selected_category = self.request.GET.get("category") or ""
        self.selected_tag = self.request.GET.get("tag") or ""

        if self.selected_category:
            qs = qs.filter(category__slug=self.selected_category)
        if self.selected_tag in {choice[0] for choice in MenuItem.Tags.choices}:
            qs = qs.filter(tag=self.selected_tag)
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = MenuCategory.objects.all()
        context["selected_category"] = self.selected_category
        context["selected_tag"] = self.selected_tag
        return context



# Cart Views
@require_POST
def add_to_cart(request, menu_item_id):
    """Add a menu item to the cart."""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to add items to cart.')
        return redirect('login')
    
    cart = Cart(request)
    menu_item = get_object_or_404(MenuItem, id=menu_item_id, is_available=True)
    quantity = int(request.POST.get('quantity', 1))
    
    cart.add(menu_item=menu_item, quantity=quantity)
    messages.success(request, f'{menu_item.name} added to cart!')
    
    # Return JSON for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': len(cart),
            'message': f'{menu_item.name} added to cart!'
        })
    
    return redirect(request.META.get('HTTP_REFERER', 'orders:home'))


@login_required
def view_cart(request):
    """Display the shopping cart."""
    cart = Cart(request)
    template = 'orders/cart_dashboard.html' if request.user.is_authenticated else 'orders/cart.html'
    return render(request, template, {'cart': cart})


@require_POST
def update_cart(request, menu_item_id):
    """Update the quantity of a menu item in the cart."""
    cart = Cart(request)
    quantity = int(request.POST.get('quantity', 1))
    
    cart.update_quantity(menu_item_id, quantity)
    messages.success(request, 'Cart updated!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price())
        })
    
    return redirect('orders:cart')


@require_POST
def remove_from_cart(request, menu_item_id):
    """Remove a menu item from the cart."""
    cart = Cart(request)
    menu_item = get_object_or_404(MenuItem, id=menu_item_id)
    
    cart.remove(menu_item)
    messages.success(request, f'{menu_item.name} removed from cart!')
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'success': True,
            'cart_count': len(cart),
            'cart_total': str(cart.get_total_price())
        })
    
    return redirect('orders:cart')


def clear_cart(request):
    """Clear all items from the cart."""
    cart = Cart(request)
    cart.clear()
    messages.success(request, 'Cart cleared!')
    return redirect('orders:cart')



# Checkout Views
def checkout(request):
    """Checkout page for placing orders."""
    if not request.user.is_authenticated:
        messages.warning(request, 'Please login to checkout.')
        return redirect('login')
    
    cart = Cart(request)
    
    if len(cart) == 0:
        messages.warning(request, 'Your cart is empty!')
        return redirect('orders:cart')
    
    if request.method == 'POST':
        from .forms import CheckoutForm
        
        form = CheckoutForm(request.POST)
        
        if form.is_valid():
            # Create order
            order = form.save(commit=False)
            order.user = request.user
            order.delivery_location = request.user.workplace
            order.phone = request.user.phone
            order.total_amount = cart.get_total_price()
            order.save()
            
            # Create order items
            for item in cart:
                OrderItem.objects.create(
                    order=order,
                    menu_item=item['menu_item'],
                    quantity=item['quantity'],
                    price=item['price']
                )
            
            # Clear cart
            cart.clear()
            
            messages.success(request, 'Your order has been placed successfully!')
            return redirect('orders:order_success', order_id=order.id)
    else:
        from .forms import CheckoutForm
        form = CheckoutForm()
    
    return render(request, 'orders/checkout.html', {
        'form': form,
        'cart': cart
    })


def order_success(request, order_id):
    """Order confirmation page."""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'orders/order_success.html', {'order': order})


# Dashboard Views
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Count
from .decorators import customer_required

@customer_required
def dashboard(request):
    """Customer dashboard home."""
    # Get user statistics
    orders = Order.objects.filter(user=request.user)
    total_orders = orders.count()
    pending_orders = orders.filter(status__in=['pending', 'confirmed', 'preparing']).count()
    total_spent = orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Get recent orders
    recent_orders = orders.order_by('-created_at')[:5]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'total_spent': total_spent,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'orders/dashboard.html', context)


@customer_required
def order_history(request):
    """Customer order history."""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'orders/order_history.html', {'orders': orders})


@customer_required
def profile(request):
    """Customer profile page."""
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name = request.POST.get('last_name', '')
        user.phone = request.POST.get('phone', '')
        user.workplace = request.POST.get('workplace', '')
        user.save()
        messages.success(request, 'Profile updated successfully!')
        return redirect('orders:profile')
    
    return render(request, 'orders/profile.html')


# Admin Dashboard Views
from .decorators import admin_required
from django.utils import timezone
from datetime import timedelta

@admin_required
def admin_dashboard(request):
    """Admin dashboard home with statistics."""
    from accounts.models import User
    from .models import ContactInquiry
    
    # Get statistics
    all_orders = Order.objects.all()
    total_orders = all_orders.count()
    pending_orders = all_orders.filter(status__in=['pending', 'confirmed', 'preparing']).count()
    
    # Today's stats
    today = timezone.now().date()
    today_orders = all_orders.filter(created_at__date=today)
    today_revenue = today_orders.aggregate(total=Sum('total_amount'))['total'] or 0
    
    # Total customers
    total_customers = User.objects.filter(role=User.Roles.CUSTOMER).count()
    
    # Inquiry statistics
    total_inquiries = ContactInquiry.objects.count()
    new_inquiries = ContactInquiry.objects.filter(status='new').count()
    
    # Recent orders
    recent_orders = all_orders.order_by('-created_at')[:10]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'today_revenue': today_revenue,
        'today_orders': today_orders.count(),
        'total_customers': total_customers,
        'total_inquiries': total_inquiries,
        'new_inquiries': new_inquiries,
        'recent_orders': recent_orders,
    }
    
    return render(request, 'orders/admin_dashboard.html', context)


@admin_required
def admin_orders(request):
    """Admin order management page with filters."""
    orders = Order.objects.all().select_related('user').prefetch_related('items')
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        orders = orders.filter(status=status_filter)
    
    # Date filter
    date_filter = request.GET.get('date', '')
    if date_filter:
        from datetime import datetime
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            orders = orders.filter(created_at__date=filter_date)
        except ValueError:
            pass
    
    # Search filter
    search = request.GET.get('search', '')
    if search:
        orders = orders.filter(
            models.Q(order_number__icontains=search) |
            models.Q(user__username__icontains=search) |
            models.Q(user__first_name__icontains=search) |
            models.Q(user__last_name__icontains=search)
        )
    
    orders = orders.order_by('-created_at')
    
    context = {
        'orders': orders,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search': search,
        'status_choices': Order.Status.choices,
    }
    
    return render(request, 'orders/admin_orders.html', context)


@admin_required
def admin_menu(request):
    """Admin menu management page."""
    menu_items = MenuItem.objects.all().select_related('category').order_by('category', 'name')
    categories = MenuCategory.objects.all()
    
    # Category filter
    category_filter = request.GET.get('category', '')
    if category_filter:
        menu_items = menu_items.filter(category__slug=category_filter)
    
    # Search filter
    search = request.GET.get('search', '')
    if search:
        menu_items = menu_items.filter(name__icontains=search)
    
    context = {
        'menu_items': menu_items,
        'categories': categories,
        'category_filter': category_filter,
        'search': search,
    }
    
    return render(request, 'orders/admin_menu.html', context)


@admin_required
def admin_customers(request):
    """Admin customer management page."""
    from accounts.models import User
    
    customers = User.objects.filter(role=User.Roles.CUSTOMER).annotate(
        total_orders=Count('orders'),
        total_spent=Sum('orders__total_amount')
    ).order_by('-total_spent')
    
    # Search filter
    search = request.GET.get('search', '')
    if search:
        customers = customers.filter(
            models.Q(username__icontains=search) |
            models.Q(first_name__icontains=search) |
            models.Q(last_name__icontains=search) |
            models.Q(email__icontains=search)
        )
    
    context = {
        'customers': customers,
        'search': search,
    }
    
    return render(request, 'orders/admin_customers.html', context)


@admin_required
@require_POST
def toggle_customer_status(request, customer_id):
    """Suspend or activate a customer account."""
    from accounts.models import User
    
    customer = get_object_or_404(User, id=customer_id, role=User.Roles.CUSTOMER)
    customer.is_active = not customer.is_active
    customer.save()
    
    status = "activated" if customer.is_active else "suspended"
    messages.success(request, f'Customer {customer.username} has been {status}')
    return redirect('orders:admin_customers')


@admin_required
@require_POST
def make_customer_admin(request, customer_id):
    """Promote a customer to admin role."""
    from accounts.models import User
    
    customer = get_object_or_404(User, id=customer_id, role=User.Roles.CUSTOMER)
    customer.role = User.Roles.ADMIN
    customer.is_staff = True
    customer.save()
    
    messages.success(request, f'{customer.username} has been promoted to admin')
    return redirect('orders:admin_customers')


@admin_required
@require_POST
def update_order_status(request, order_id):
    """Update order status."""
    order = get_object_or_404(Order, id=order_id)
    new_status = request.POST.get('status')
    
    if new_status in dict(Order.Status.choices):
        order.status = new_status
        order.save()
        messages.success(request, f'Order {order.order_number} status updated to {order.get_status_display()}')
    else:
        messages.error(request, 'Invalid status')
    
    return redirect('orders:admin_orders')


@admin_required
@require_POST
def toggle_menu_availability(request, item_id):
    """Toggle menu item availability."""
    import json
    menu_item = get_object_or_404(MenuItem, id=item_id)
    data = json.loads(request.body)
    menu_item.is_available = data.get('is_available', False)
    menu_item.save()
    return JsonResponse({'success': True})


@admin_required
def add_menu_item(request):
    """Add new menu item."""
    from .forms import MenuItemForm
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item added successfully!')
            return redirect('orders:admin_menu')
    else:
        form = MenuItemForm()
    
    return render(request, 'orders/menu_item_form.html', {
        'form': form,
        'title': 'Add Menu Item',
        'button_text': 'Add Item'
    })


@admin_required
def edit_menu_item(request, item_id):
    """Edit existing menu item."""
    from .forms import MenuItemForm
    
    menu_item = get_object_or_404(MenuItem, id=item_id)
    
    if request.method == 'POST':
        form = MenuItemForm(request.POST, request.FILES, instance=menu_item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Menu item updated successfully!')
            return redirect('orders:admin_menu')
    else:
        form = MenuItemForm(instance=menu_item)
    
    return render(request, 'orders/menu_item_form.html', {
        'form': form,
        'title': 'Edit Menu Item',
        'button_text': 'Update Item',
        'menu_item': menu_item
    })


@admin_required
@require_POST
def delete_menu_item(request, item_id):
    """Delete a menu item and all related order items."""
    menu_item = get_object_or_404(MenuItem, id=item_id)
    item_name = menu_item.name
    
    # Delete all related order items first
    menu_item.order_items.all().delete()
    
    # Now delete the menu item
    menu_item.delete()
    messages.success(request, f'{item_name} has been deleted successfully!')
    return redirect('orders:admin_menu')


@admin_required
def admin_reports(request):
    """Admin reports and analysis page."""
    from accounts.models import User
    from django.db.models.functions import TruncDate
    from datetime import datetime, timedelta
    import json
    from decimal import Decimal
    
    # Date range filter
    period = request.GET.get('period', '7')  # Default 7 days
    try:
        days = int(period)
    except ValueError:
        days = 7
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Revenue over time
    daily_revenue = Order.objects.filter(
        created_at__gte=start_date
    ).annotate(
        date=TruncDate('created_at')
    ).values('date').annotate(
        revenue=Sum('total_amount'),
        order_count=Count('id')
    ).order_by('date')
    
    # Convert to JSON-serializable format
    daily_revenue_list = [
        {
            'date': item['date'].isoformat(),
            'revenue': float(item['revenue']) if item['revenue'] else 0,
            'order_count': item['order_count']
        }
        for item in daily_revenue
    ]
    
    # Total metrics
    total_orders = Order.objects.filter(created_at__gte=start_date).count()
    total_revenue = Order.objects.filter(created_at__gte=start_date).aggregate(
        total=Sum('total_amount')
    )['total'] or 0
    
    avg_order_value = total_revenue / total_orders if total_orders > 0 else 0
    
    # Order status breakdown
    status_breakdown = list(Order.objects.filter(
        created_at__gte=start_date
    ).values('status').annotate(
        count=Count('id')
    ).order_by('-count'))
    
    # Top selling items
    top_items = OrderItem.objects.filter(
        order__created_at__gte=start_date
    ).values(
        'menu_item__name',
        'menu_item__category__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(models.F('quantity') * models.F('price'))
    ).order_by('-total_quantity')[:10]
    
    # Top customers
    top_customers = User.objects.filter(
        role=User.Roles.CUSTOMER,
        orders__created_at__gte=start_date
    ).annotate(
        order_count=Count('orders'),
        total_spent=Sum('orders__total_amount')
    ).order_by('-total_spent')[:10]
    
    # Category performance
    category_performance = OrderItem.objects.filter(
        order__created_at__gte=start_date
    ).values(
        'menu_item__category__name'
    ).annotate(
        total_quantity=Sum('quantity'),
        total_revenue=Sum(models.F('quantity') * models.F('price'))
    ).order_by('-total_revenue')
    
    # Payment method breakdown
    payment_breakdown_raw = Order.objects.filter(
        created_at__gte=start_date
    ).values('payment_method').annotate(
        count=Count('id'),
        revenue=Sum('total_amount')
    ).order_by('-count')
    
    payment_breakdown_list = [
        {
            'payment_method': item['payment_method'],
            'count': item['count'],
            'revenue': float(item['revenue']) if item['revenue'] else 0
        }
        for item in payment_breakdown_raw
    ]
    
    # Peak hours analysis
    hourly_orders = list(Order.objects.filter(
        created_at__gte=start_date
    ).extra(
        select={'hour': 'CAST(strftime("%%H", created_at) AS INTEGER)'}
    ).values('hour').annotate(
        count=Count('id')
    ).order_by('hour'))
    
    context = {
        'period': days,
        'start_date': start_date,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
        'avg_order_value': avg_order_value,
        'daily_revenue': json.dumps(daily_revenue_list),
        'status_breakdown': json.dumps(status_breakdown),
        'top_items': list(top_items),
        'top_customers': list(top_customers),
        'category_performance': list(category_performance),
        'payment_breakdown': json.dumps(payment_breakdown_list),
        'hourly_orders': json.dumps(hourly_orders),
    }
    
    return render(request, 'orders/admin_reports.html', context)



# Contact Views
def contact_page(request):
    """Contact page with form for customer inquiries."""
    if request.method == 'POST':
        from .forms import ContactForm
        from django.core.mail import send_mail
        from django.conf import settings
        import logging
        
        logger = logging.getLogger(__name__)
        form = ContactForm(request.POST)
        
        if form.is_valid():
            inquiry = form.save()
            
            # Send email notification
            try:
                subject = f"New Contact Inquiry from {inquiry.name}"
                message = f"""
New inquiry received from SmartKibandaski website

Customer Details:
- Name: {inquiry.name}
- Email: {inquiry.email}
- Phone: {inquiry.phone}

Inquiry Type: {inquiry.get_subject_type_display()}
Order Number: {inquiry.order_number or 'N/A'}

Message:
{inquiry.message}

Submitted: {inquiry.created_at.strftime('%Y-%m-%d %H:%M:%S')}

View in admin dashboard: http://localhost:8000/admin/inquiries/
"""
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.ADMIN_EMAIL],
                    fail_silently=False,
                    html_message=None,
                )
                
                messages.success(request, 'Thank you for contacting us! We will get back to you soon.')
            except Exception as e:
                logger.error(f"Failed to send inquiry email: {e}")
                messages.warning(request, 'Your inquiry has been saved, but there was an issue sending the notification. We will still review your message.')
            
            return redirect('orders:contact')
    else:
        from .forms import ContactForm
        form = ContactForm()
    
    return render(request, 'orders/contact.html', {'form': form})


# Admin Inquiries Views
@admin_required
def admin_inquiries(request):
    """Admin page for managing customer inquiries."""
    from .models import ContactInquiry
    
    inquiries = ContactInquiry.objects.all()
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        inquiries = inquiries.filter(status=status_filter)
    
    # Date filter
    date_filter = request.GET.get('date', '')
    if date_filter:
        from datetime import datetime
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
            inquiries = inquiries.filter(created_at__date=filter_date)
        except ValueError:
            pass
    
    # Search filter
    search = request.GET.get('search', '')
    if search:
        inquiries = inquiries.filter(
            models.Q(name__icontains=search) |
            models.Q(email__icontains=search)
        )
    
    context = {
        'inquiries': inquiries,
        'status_filter': status_filter,
        'date_filter': date_filter,
        'search': search,
        'status_choices': ContactInquiry.Status.choices,
    }
    
    return render(request, 'orders/admin_inquiries.html', context)


@admin_required
@require_POST
def update_inquiry_status(request, inquiry_id):
    """Update inquiry status via AJAX."""
    from .models import ContactInquiry
    import json
    
    inquiry = get_object_or_404(ContactInquiry, id=inquiry_id)
    data = json.loads(request.body)
    new_status = data.get('status')
    
    if new_status in dict(ContactInquiry.Status.choices):
        inquiry.status = new_status
        inquiry.save()
        return JsonResponse({'success': True, 'status': inquiry.get_status_display()})
    else:
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)


@admin_required
def debug_images(request):
    """Debug view to check image configuration - REMOVE IN PRODUCTION"""
    from django.http import JsonResponse
    from django.conf import settings
    import os
    
    debug_info = {
        'environment': {
            'RENDER': os.environ.get('RENDER'),
            'DEBUG': settings.DEBUG,
            'DEFAULT_FILE_STORAGE': getattr(settings, 'DEFAULT_FILE_STORAGE', 'Not set'),
            'MEDIA_URL': settings.MEDIA_URL,
            'MEDIA_ROOT': str(settings.MEDIA_ROOT),
        },
        'cloudinary': {
            'CLOUD_NAME': getattr(settings, 'CLOUDINARY_STORAGE', {}).get('CLOUD_NAME', 'Not set'),
            'API_KEY': getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_KEY', 'Not set'),
            'API_SECRET_SET': bool(getattr(settings, 'CLOUDINARY_STORAGE', {}).get('API_SECRET')),
        },
        'menu_items': []
    }
    
    # Get menu items with images
    items_with_images = MenuItem.objects.filter(image__isnull=False).exclude(image='')[:5]  # Limit to 5
    
    for item in items_with_images:
        item_info = {
            'name': item.name,
            'image_name': item.image.name if item.image else None,
        }
        
        try:
            item_info['image_url'] = item.image.url
        except Exception as e:
            item_info['image_url_error'] = str(e)
            
        debug_info['menu_items'].append(item_info)
    
    return JsonResponse(debug_info, indent=2)