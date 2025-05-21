from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    UnidadViewSet,
    LoginView,
    LogoutView,
    VerifyAccessView,
)

app_name = 'accounts'

# Configuración del router para ViewSets
router = DefaultRouter()
router.register(r'accounts/users', UserViewSet)
router.register(r'accounts/unidades', UnidadViewSet)

# URLs de la API v1
api_v1_patterns = [
    path('', include(router.urls)),
    path('accounts/login/', LoginView.as_view(), name='api-login'),
    path('accounts/logout/', LogoutView.as_view(), name='api-logout'),
    path('accounts/verify-access/', VerifyAccessView.as_view(), name='verify-access'),
]

urlpatterns = [
    # API v1
    path('api/v1/', include(api_v1_patterns)),
]