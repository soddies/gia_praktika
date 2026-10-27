from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_views, name='login'),
    path('', views.main_views, name='main'),
    path('logout/', views.logout_views, name='logout'),

    path('api/products/', views.api_products, name='api_products'),

    path('product/add/', views.product_form_view, name='product_add'),
    path('product/edit/<int:product_id>/', views.product_form_view, name='product_edit'),

    path('product/delete/<int:product_id>/', views.product_delete_view, name='product_delete',),
    
    path('orders/', views.orders_list, name='orders_list'),
]