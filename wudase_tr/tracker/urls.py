from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_view, name='upload_view'),
    path('recall/', views.daily_recall, name='daily_recall'),
]