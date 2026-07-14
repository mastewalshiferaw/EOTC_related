from django.urls import path
from .views import DocumentUploadView
from .views import DirectTranslateView

urlpatterns = [
    path('upload/', DocumentUploadView.as_view(), name='document-upload'),
     path('translate-text/', DirectTranslateView.as_view(), name='direct-translate'),
]