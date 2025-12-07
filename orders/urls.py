from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('menu/', views.MenuListView.as_view(), name='menu'),
    
    # Cart URLs
    path('cart/', views.view_cart, name='cart'),
    path('cart/add/<int:menu_item_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/<int:menu_item_id>/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:menu_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/clear/', views.clear_cart, name='clear_cart'),
    
    # Checkout URLs
    path('checkout/', views.checkout, name='checkout'),
    path('order/<int:order_id>/success/', views.order_success, name='order_success'),
    
    # Dashboard URLs
    path('dashboard/', views.dashboard, name='dashboard'),
    path('orders/', views.order_history, name='order_history'),
    path('profile/', views.profile, name='profile'),
    
    # Admin Dashboard URLs
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin-dashboard/orders/', views.admin_orders, name='admin_orders'),
    path('admin-dashboard/orders/<int:order_id>/update-status/', views.update_order_status, name='update_order_status'),
    path('admin-dashboard/menu/', views.admin_menu, name='admin_menu'),
    path('admin-dashboard/menu/<int:item_id>/toggle-availability/', views.toggle_menu_availability, name='toggle_menu_availability'),
    path('admin-dashboard/customers/', views.admin_customers, name='admin_customers'),
]

