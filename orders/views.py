from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import ListView, TemplateView

from .cart import Cart
from .models import MenuCategory, MenuItem


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
    template_name = 'orders/menu_list.html'
    context_object_name = 'menu_items'

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


def view_cart(request):
    """Display the shopping cart."""
    cart = Cart(request)
    return render(request, 'orders/cart.html', {'cart': cart})


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
