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
        items = MenuItem.objects.filter(is_available=True)[:6]

        context["categories"] = categories
        context["menu_items"] = items
        context["selected_category"] = None
        context["selected_tag"] = None
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
    
    # Recent orders
    recent_orders = all_orders.order_by('-created_at')[:10]
    
    context = {
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'today_revenue': today_revenue,
        'today_orders': today_orders.count(),
        'total_customers': total_customers,
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
