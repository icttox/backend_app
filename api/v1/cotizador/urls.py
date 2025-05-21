from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.cotizador.views import (
    CotizacionViewSet,
    DetalleCotizacionViewSet,
    ProductTemplateViewSet,
    ImagenProductoViewSet,
    BuscarProductosView,
    AgregarProductoCotizacionView,
    get_product_data
)

app_name = 'api-v1-cotizador'

# Router para ViewSets
router = DefaultRouter()
router.register(r'cotizaciones', CotizacionViewSet, basename='cotizacion')
router.register(r'detalles', DetalleCotizacionViewSet, basename='detalle-cotizacion')
router.register(r'templates', ProductTemplateViewSet, basename='product-template')
router.register(r'imagenes', ImagenProductoViewSet, basename='imagen-producto')

# URLs adicionales
urlpatterns = [
    path('', include(router.urls)),
    # Rutas específicas para templates
    path('templates/grupos/', ProductTemplateViewSet.as_view({'get': 'grupos'}), name='template-grupos'),
    path('templates/familias/', ProductTemplateViewSet.as_view({'get': 'familias'}), name='template-familias'),
    path('templates/lineas/', ProductTemplateViewSet.as_view({'get': 'lineas'}), name='template-lineas'),
    # Rutas de productos
    path('productos/buscar/', 
        BuscarProductosView.as_view(), 
        name='buscar-productos'
    ),
    path('productos/agregar/', 
        AgregarProductoCotizacionView.as_view(), 
        name='agregar-producto'
    ),
    path('productos/data/',
        get_product_data,
        name='get-product-data'
    ),
]
