from django.db import models
from django.contrib.auth.models import User
from django.db.models import Count, Sum, Avg
from django.utils import timezone
from datetime import timedelta
import json

# Create your models here.

class GroceryList(models.Model):
    name = models.CharField(max_length=100)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='grocery_lists', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username if self.user else 'No User'})"

    class Meta:
        ordering = ['-created_at']

    @property
    def total(self):
        return sum(item.total_price or 0 for item in self.items.all())

    def get_spending_over_time(self):
        """Returns daily spending data for the last 30 days"""
        thirty_days_ago = timezone.now() - timedelta(days=30)
        items = self.items.filter(
            created_at__gte=thirty_days_ago,
            is_purchased=True,
            price__isnull=False
        )
        
        spending_by_date = {}
        for item in items:
            date_str = item.created_at.date().isoformat()
            spending_by_date[date_str] = spending_by_date.get(date_str, 0) + (item.total_price or 0)
        
        return spending_by_date

    def get_most_purchased_items(self, limit=5):
        """Returns the most frequently purchased items"""
        return self.items.filter(
            is_purchased=True
        ).values('name').annotate(
            count=Count('id'),
            avg_price=Avg('price')
        ).order_by('-count')[:limit]

    def get_purchase_by_weekday(self):
        """Returns purchase frequency by day of week"""
        return self.items.filter(
            is_purchased=True
        ).extra(
            select={'weekday': "EXTRACT(DOW FROM created_at)"}
        ).values('weekday').annotate(
            count=Count('id')
        ).order_by('weekday')

    def get_price_trends(self, item_name):
        """Returns price trends for a specific item over time"""
        return self.items.filter(
            name=item_name,
            is_purchased=True,
            price__isnull=False
        ).values('created_at', 'price').order_by('created_at')

class GroceryItem(models.Model):
    list = models.ForeignKey(GroceryList, related_name='items', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    is_purchased = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    used_date = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.list.name})"

    class Meta:
        ordering = ['created_at']

    @property
    def total_price(self):
        if self.price is None:
            return None
        return self.price * self.quantity
