from django.contrib import admin
from .models import Product, Webhook

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('sku', 'name', 'price', 'active', 'updated_at')
    search_fields = ('sku', 'name', 'description')

@admin.register(Webhook)
class WebhookAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'active', 'created_at')
    search_fields = ('name', 'url')
