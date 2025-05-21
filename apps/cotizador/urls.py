from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CotizacionViewSet,
    ProductoCotizacionViewSet,
    CotizadorImagenproductoViewSet,
    KitViewSet,
    KitProductoViewSet,
    SyncViewSet
)

# Crear dos routers, uno con slash y otro sin slash
router_no_slash = DefaultRouter(trailing_slash=False)
router_with_slash = DefaultRouter(trailing_slash=True)

# Registrar las vistas en ambos routers
for router in [router_no_slash, router_with_slash]:
    router.register(r'cotizaciones', CotizacionViewSet)
    router.register(r'productos-cotizacion', ProductoCotizacionViewSet)
    router.register(r'imagenes-producto', CotizadorImagenproductoViewSet)
    router.register(r'kits', KitViewSet)
    router.register(r'kit-productos', KitProductoViewSet)
    router.register(r'sync', SyncViewSet, basename='sync')

urlpatterns = [
    # Incluir ambos routers
    path('', include(router_no_slash.urls)),
    path('', include(router_with_slash.urls)),
]
