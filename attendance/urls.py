from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('checkin/', views.checkin, name='checkin'),
    path('checkout/', views.quick_checkout, name='quick_checkout'),
    path('login/', views.dashboard_login, name='dashboard_login'),
    path('logout/', views.dashboard_logout, name='dashboard_logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('export/', views.export_csv, name='export_csv'),
]
