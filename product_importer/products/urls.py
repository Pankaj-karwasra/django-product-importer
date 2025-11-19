from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('upload/', views.upload_csv, name='upload_csv'),
    path('upload-status/<task_id>/', views.upload_status, name='upload_status'),
    path('products/', views.ProductListCreateView.as_view(), name='product_list_create'),
    path('products/<int:pk>/', views.ProductRetrieveUpdateDestroyView.as_view(), name='product_detail'),
    path('products/bulk-delete/', views.bulk_delete_products, name='bulk_delete'),
    path('webhooks/', views.WebhookListCreateView.as_view(), name='webhook_list_create'),
    path('webhooks/<int:pk>/', views.WebhookRetrieveUpdateDestroyView.as_view(), name='webhook_detail'),
    path('webhooks/test/<int:pk>/', views.webhook_test, name='webhook_test'),
    path('ui/', views.ui_view, name='ui'),
]
