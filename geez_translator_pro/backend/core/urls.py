from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from translator.views import HealthCheckView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('healthz', HealthCheckView.as_view(), name='healthz-no-slash'),
    path('healthz/', HealthCheckView.as_view(), name='healthz'),
    path('health/', HealthCheckView.as_view(), name='health'),
    path('api/', include('translator.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
