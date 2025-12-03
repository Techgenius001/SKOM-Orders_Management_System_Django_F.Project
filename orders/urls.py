from django.urls import path

from . import views

app_name = 'orders'

urlpatterns = [
    path('', views.HomeView.as_view(), name='home'),
    path('menu/', views.MenuListView.as_view(), name='menu'),
]

