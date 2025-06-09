from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .email_check import CheckEmailAPIView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Endpoint público para verificar emails (accesible sin autenticación)
    path('api/v1/check-email/', CheckEmailAPIView.as_view(), name='public-check-email'),
    
    # API v1 URLs
    path('api/v1/analytics/', include('apps.analytics.urls')),
    path('api/v1/', include([
        path('accounts/', include('apps.accounts.urls_api')),
        path('cotizador/', include([
            path('productos/', include('apps.cotizador.cache.urls')),  # URLs de productos en caché
            path('', include('apps.cotizador.urls')),  # Otras URLs del cotizador
        ])),
        path('compras/', include('apps.compras.urls')),  # URLs de la app de compras
        path('aip/', include('apps.aip.urls')),  # URLs de la app de AIP
        path('analytics/', include('apps.analytics.urls')),  # URLs de la app de Analytics
    ])),
    
    # URLs de templates
    path('accounts/', include('apps.accounts.urls')),
]

# Serve static and media files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
