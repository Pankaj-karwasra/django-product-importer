from django.db import models
from django.db.models.functions import Lower

class Product(models.Model):
    sku = models.CharField(max_length=255)
    name = models.CharField(max_length=1024, blank=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        constraints = [
            models.UniqueConstraint(
                Lower('sku'),
                name='unique_lower_sku'
            )
        ]

    def __str__(self):
        return f"{self.sku} - {self.name}"

class Webhook(models.Model):
    EVENT_CHOICES = [
        ('product.created', 'Product Created'),
        ('product.updated', 'Product Updated'),
        ('product.deleted', 'Product Deleted'),
    ]
    url = models.URLField()
    events = models.JSONField(default=list)  # store list of events
    active = models.BooleanField(default=True)
    name = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name or self.url
