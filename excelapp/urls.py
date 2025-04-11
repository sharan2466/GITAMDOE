from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('compare/', views.compare_excel, name='compare_excel'),
]
