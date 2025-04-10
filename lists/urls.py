from django.urls import path
from . import views

app_name = 'lists'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('list/<int:pk>/', views.list_detail, name='list_detail'),
    path('list/create/', views.create_list, name='create_list'),
    path('list/<int:pk>/delete/', views.delete_list, name='delete_list'),
    path('item/<int:pk>/update/', views.update_item, name='update_item'),
    path('item/<int:pk>/delete/', views.delete_item, name='delete_item'),
] 