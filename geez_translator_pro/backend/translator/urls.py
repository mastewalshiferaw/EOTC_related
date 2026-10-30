from django.urls import path
from .views import OCROnlyView, CleanOCRView, TranslateFlexibleView, HealthCheckView

urlpatterns = [
    path('health/', HealthCheckView.as_view(), name='api-health'),
    path('ocr-only/', OCROnlyView.as_view(), name='ocr-only'),
    path('clean-ocr/', CleanOCRView.as_view(), name='clean-ocr'),
    path('translate-flexible/', TranslateFlexibleView.as_view(), name='translate-flexible'),
]
