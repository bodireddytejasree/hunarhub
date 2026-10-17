from django.urls import path

from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('browse/', views.browse, name='browse'),
    path('entrepreneur/<int:pk>/', views.entrepreneur_detail, name='entrepreneur_detail'),
    path('services/<int:pk>/request/', views.request_service, name='request_service'),
    path('products/<int:pk>/buy/', views.buy_product, name='buy_product'),
    path('entrepreneur/<int:pk>/review/', views.add_review, name='add_review'),
    path('entrepreneur/<int:pk>/complaint/', views.file_complaint, name='file_complaint'),

    path('me/orders/', views.customer_dashboard, name='customer_dashboard'),
    path('me/business/', views.entrepreneur_dashboard, name='entrepreneur_dashboard'),
    path('me/business/profile/', views.profile_edit, name='profile_edit'),
    path('me/business/availability/', views.toggle_availability, name='toggle_availability'),
    path('me/business/services/add/', views.service_form, name='service_form'),
    path('me/business/services/<int:pk>/edit/', views.service_form, name='service_form'),
    path('me/business/products/add/', views.product_form, name='product_form'),
    path('me/business/products/<int:pk>/edit/', views.product_form, name='product_form'),
    path('me/business/<str:kind>/<int:pk>/remove/', views.item_remove, name='item_remove'),
    path('requests/<int:pk>/<str:action>/', views.request_action, name='request_action'),
    path('orders/<int:pk>/<str:action>/', views.order_action, name='order_action'),

    path('manage/', views.admin_dashboard, name='admin_dashboard'),
    path('manage/entrepreneurs/<int:pk>/<str:action>/', views.admin_verify, name='admin_verify'),
    path('manage/categories/add/', views.category_add, name='category_add'),
    path('manage/categories/<int:pk>/delete/', views.category_delete, name='category_delete'),
    path('manage/complaints/<int:pk>/resolve/', views.complaint_resolve, name='complaint_resolve'),
]
