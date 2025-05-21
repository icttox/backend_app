from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoriaViewSet,
    UserComprasViewSet,
    AlmacenViewSet,
    CategoriaProductoViewSet,
    PronosticoExistenciasAPIView,
    PropuestaCompraViewSet,
    ItemPropuestaCompraViewSet,
    ProveedorViewSet
)

router = DefaultRouter()
router.register(r'categorias', CategoriaViewSet)
router.register(r'compradores', UserComprasViewSet, basename='comprador-perfil')
router.register(r'almacenes', AlmacenViewSet, basename='almacenes')
router.register(r'proveedores', ProveedorViewSet, basename='proveedores')
router.register(r'propuestas', PropuestaCompraViewSet)
router.register(r'items-propuesta', ItemPropuestaCompraViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('pronostico-existencias/', PronosticoExistenciasAPIView.as_view(), name='pronostico-existencias'),
    path('categorias-productos/', CategoriaProductoViewSet.as_view(), name='categorias-productos'),
]
