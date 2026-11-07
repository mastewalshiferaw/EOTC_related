from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('upload/', views.upload_view, name='upload_view'),
    path('recall/', views.daily_recall, name='daily_recall'),
    path('paragraph/<int:pk>/edit/', views.edit_paragraph, name='edit_paragraph'),
    path('paragraph/<int:pk>/delete/', views.delete_paragraph, name='delete_paragraph'),
]