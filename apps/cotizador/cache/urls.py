from rest_framework.routers import DefaultRouter
from .views import ProductsCacheViewSet

# Crear el router
router = DefaultRouter()
router.register('', ProductsCacheViewSet, basename='products-cache')

urlpatterns = router.urls
