"""Custom decorators for access control."""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """Decorator to restrict access to admin users only."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Allow superusers, staff, and users with admin role
        if not (request.user.is_superuser or request.user.is_staff or request.user.is_admin_role):
            messages.error(request, 'Access denied. Admin privileges required.')
            return redirect('orders:dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper


def customer_required(view_func):
    """Decorator to restrict access to customer users only."""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Block superusers, staff, and users with admin role
        if request.user.is_superuser or request.user.is_staff or request.user.is_admin_role:
            messages.error(request, 'Access denied. This is a customer-only area.')
            return redirect('orders:admin_dashboard')
        return view_func(request, *args, **kwargs)
    return wrapper
