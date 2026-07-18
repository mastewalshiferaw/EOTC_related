from django.urls import path
from .views import OCROnlyView, TranslateDualView

urlpatterns = [
    path('ocr-only/', OCROnlyView.as_view()),
    path('translate-dual/', TranslateDualView.as_view()),
]