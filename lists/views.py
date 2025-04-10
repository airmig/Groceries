from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import GroceryList, GroceryItem
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.utils import timezone
from decimal import Decimal
import decimal
from django.db.models import Sum
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login
from datetime import timedelta, datetime

class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, (datetime, timezone.datetime)):
            return obj.isoformat()
        if isinstance(obj, timezone.date):
            return obj.isoformat()
        return super().default(obj)

def register(request):
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('lists:home')
    else:
        form = UserCreationForm()
    return render(request, 'lists/register.html', {'form': form})

@login_required
def home(request):
    lists = GroceryList.objects.filter(user=request.user)
    
    # Get statistics data from all lists
    stats = {
        'spending_over_time': {},
        'most_purchased': [],
        'purchase_by_weekday': [],
        'price_trends': {}
    }
    
    # Combine statistics from all lists
    for grocery_list in lists:
        # Spending over time
        list_spending = grocery_list.get_spending_over_time()
        for date, amount in list_spending.items():
            stats['spending_over_time'][date] = stats['spending_over_time'].get(date, 0) + amount
        
        # Most purchased items
        list_most_purchased = list(grocery_list.get_most_purchased_items())
        for item in list_most_purchased:
            # Check if item already exists in the combined list
            existing_item = next((i for i in stats['most_purchased'] if i['name'] == item['name']), None)
            if existing_item:
                existing_item['count'] += item['count']
                existing_item['avg_price'] = (existing_item['avg_price'] + item['avg_price']) / 2
            else:
                stats['most_purchased'].append(item)
        
        # Purchase by weekday
        list_weekday = list(grocery_list.get_purchase_by_weekday())
        for day in list_weekday:
            # Check if weekday already exists in the combined list
            existing_day = next((d for d in stats['purchase_by_weekday'] if d['weekday'] == day['weekday']), None)
            if existing_day:
                existing_day['count'] += day['count']
            else:
                stats['purchase_by_weekday'].append(day)
    
    # Sort most purchased items by count
    stats['most_purchased'] = sorted(stats['most_purchased'], key=lambda x: x['count'], reverse=True)[:5]
    
    # Get price trends for most purchased items
    most_purchased_items = [item['name'] for item in stats['most_purchased']]
    for item_name in most_purchased_items:
        item_trends = []
        for grocery_list in lists:
            item_trends.extend(list(grocery_list.get_price_trends(item_name)))
        stats['price_trends'][item_name] = sorted(item_trends, key=lambda x: x['created_at'])
    
    # Add sample data if no real data exists
    if not stats['spending_over_time']:
        # Add sample spending data for the last 7 days
        today = timezone.now().date()
        for i in range(7):
            date = today - timedelta(days=i)
            stats['spending_over_time'][date.isoformat()] = round(10 + i * 5, 2)
    
    if not stats['most_purchased']:
        # Add sample most purchased items
        stats['most_purchased'] = [
            {'name': 'Milk', 'count': 5, 'avg_price': 3.99},
            {'name': 'Bread', 'count': 4, 'avg_price': 2.49},
            {'name': 'Eggs', 'count': 3, 'avg_price': 4.99},
            {'name': 'Butter', 'count': 2, 'avg_price': 3.49},
            {'name': 'Cheese', 'count': 2, 'avg_price': 5.99}
        ]
    
    if not stats['purchase_by_weekday']:
        # Add sample weekday data
        stats['purchase_by_weekday'] = [
            {'weekday': 0, 'count': 3},  # Sunday
            {'weekday': 1, 'count': 2},  # Monday
            {'weekday': 2, 'count': 4},  # Tuesday
            {'weekday': 3, 'count': 1},  # Wednesday
            {'weekday': 4, 'count': 5},  # Thursday
            {'weekday': 5, 'count': 6},  # Friday
            {'weekday': 6, 'count': 2}   # Saturday
        ]
    
    # Add sample price trends for most purchased items
    if not stats['price_trends']:
        for item in stats['most_purchased']:
            item_name = item['name']
            stats['price_trends'][item_name] = []
            # Add 5 sample price points over the last 30 days
            for i in range(5):
                date = today - timedelta(days=i * 7)
                price = round(item['avg_price'] * (1 + (i % 2) * 0.1), 2)  # Alternate between normal and 10% higher price
                stats['price_trends'][item_name].append({
                    'created_at': date.isoformat(),
                    'price': price
                })
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            grocery_list = GroceryList.objects.create(user=request.user, name=name)
            return JsonResponse({
                'id': grocery_list.id,
                'name': grocery_list.name,
                'created_at': grocery_list.created_at.isoformat(),
            })
    
    context = {
        'lists': lists,
        'stats': json.dumps(stats, cls=CustomJSONEncoder),
        'weekdays': json.dumps(['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']),
    }
    return render(request, 'lists/home.html', context)

@login_required
def list_detail(request, pk):
    grocery_list = get_object_or_404(GroceryList, pk=pk, user=request.user)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        if name:
            item = GroceryItem.objects.create(list=grocery_list, name=name)
            
            # Calculate the item's total price
            total_price = None
            if item.price is not None:
                total_price = item.price * item.quantity
                
            # Refresh the list to get the updated total
            grocery_list.refresh_from_db()
            
            return JsonResponse({
                'id': item.id,
                'name': item.name,
                'is_purchased': item.is_purchased,
                'is_used': item.is_used,
                'price': str(item.price) if item.price else None,
                'quantity': item.quantity,
                'total': str(total_price) if total_price else None,
                'list_total': str(grocery_list.total)
            })
            
    context = {
        'grocery_list': grocery_list,
    }
    return render(request, 'lists/list_detail.html', context)

@login_required
@require_POST
def create_list(request):
    data = json.loads(request.body)
    name = data.get('name')
    if name:
        grocery_list = GroceryList.objects.create(user=request.user, name=name)
        return JsonResponse({'id': grocery_list.id, 'name': grocery_list.name})
    return JsonResponse({'error': 'Name is required'}, status=400)

@login_required
@require_POST
def delete_list(request, pk):
    grocery_list = get_object_or_404(GroceryList, pk=pk, user=request.user)
    grocery_list.delete()
    return JsonResponse({'success': True})

@login_required
@require_POST
def delete_item(request, pk):
    item = get_object_or_404(GroceryItem, pk=pk)
    list_id = item.list.id
    list = get_object_or_404(GroceryList, pk=list_id, user=request.user)
    item.delete()
    return JsonResponse({'list_total': str(list.total)})

@login_required
@require_POST
def update_item(request, pk):
    item = get_object_or_404(GroceryItem, pk=pk)
    list = get_object_or_404(GroceryList, pk=item.list.id, user=request.user)
    data = json.loads(request.body)
    
    if 'is_purchased' in data:
        item.is_purchased = data['is_purchased']
    if 'is_used' in data:
        item.is_used = data['is_used']
        if data['is_used']:
            item.used_date = timezone.now()
        else:
            item.used_date = None
    if 'price' in data:
        try:
            price_str = data['price']
            if price_str and price_str.strip():
                item.price = Decimal(price_str)
            else:
                item.price = None
        except (ValueError, TypeError, decimal.InvalidOperation):
            item.price = None
    if 'quantity' in data:
        try:
            qty_str = data['quantity']
            if qty_str and str(qty_str).strip():
                item.quantity = max(1, int(qty_str))
            else:
                item.quantity = 1
        except (ValueError, TypeError):
            item.quantity = 1
    
    item.save()

    # Calculate the item's total price
    total_price = None
    if item.price is not None:
        total_price = item.price * item.quantity

    # Refresh the list to get the updated total
    grocery_list = item.list
    grocery_list.refresh_from_db()

    return JsonResponse({
        'id': item.id,
        'is_purchased': item.is_purchased,
        'is_used': item.is_used,
        'used_date': item.used_date.isoformat() if item.used_date else None,
        'price': str(item.price) if item.price else None,
        'quantity': item.quantity,
        'total': str(total_price) if total_price else None,
        'list_total': str(grocery_list.total)
    })
