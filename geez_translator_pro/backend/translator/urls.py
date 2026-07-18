from django.urls import path
from .views import OCROnlyView, TranslateDualView

urlpatterns = [
    path('ocr-only/', OCROnlyView.as_view()),
    path('translate-flexible/', TranslateFlexibleView.as_view(), name='translate-flexible'),
]