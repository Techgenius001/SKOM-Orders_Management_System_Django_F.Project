"""
Shopping cart functionality using Django sessions.
"""
from decimal import Decimal
from django.conf import settings
from .models import MenuItem


class Cart:
    """Session-based shopping cart."""

    def __init__(self, request):
        """Initialize the cart."""
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            # Save an empty cart in the session
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, menu_item, quantity=1, override_quantity=False):
        """
        Add a menu item to the cart or update its quantity.
        
        Args:
            menu_item: MenuItem instance
            quantity: int, quantity to add
            override_quantity: bool, if True replace quantity instead of adding
        """
        menu_item_id = str(menu_item.id)
        if menu_item_id not in self.cart:
            self.cart[menu_item_id] = {
                'quantity': 0,
                'price': str(menu_item.price)
            }
        
        if override_quantity:
            self.cart[menu_item_id]['quantity'] = quantity
        else:
            self.cart[menu_item_id]['quantity'] += quantity
        
        self.save()

    def save(self):
        """Mark the session as modified to ensure it's saved."""
        self.session.modified = True

    def remove(self, menu_item):
        """Remove a menu item from the cart."""
        menu_item_id = str(menu_item.id)
        if menu_item_id in self.cart:
            del self.cart[menu_item_id]
            self.save()

    def update_quantity(self, menu_item_id, quantity):
        """Update the quantity of a menu item."""
        menu_item_id = str(menu_item_id)
        if menu_item_id in self.cart:
            if quantity > 0:
                self.cart[menu_item_id]['quantity'] = quantity
            else:
                del self.cart[menu_item_id]
            self.save()

    def __iter__(self):
        """
        Iterate over the items in the cart and get the menu items from the database.
        """
        menu_item_ids = self.cart.keys()
        # Get the menu item objects and add them to the cart
        menu_items = MenuItem.objects.filter(id__in=menu_item_ids)
        cart = self.cart.copy()
        
        for menu_item in menu_items:
            cart[str(menu_item.id)]['menu_item'] = menu_item
        
        for item in cart.values():
            item['price'] = Decimal(item['price'])
            item['total_price'] = item['price'] * item['quantity']
            yield item

    def __len__(self):
        """Count all items in the cart."""
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        """Calculate the total price of all items in the cart."""
        return sum(
            Decimal(item['price']) * item['quantity']
            for item in self.cart.values()
        )

    def clear(self):
        """Remove cart from session."""
        del self.session[settings.CART_SESSION_ID]
        self.save()

    def get_item_count(self):
        """Get the number of unique items in the cart."""
        return len(self.cart)
