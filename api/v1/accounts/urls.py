from django.urls import path
from apps.accounts.views import (
    UserViewSet,
    UnidadViewSet,
    LoginView,
    LogoutView,
    VerifyAccessView,
    QuotationView
)
from rest_framework_simplejwt.views import TokenRefreshView, TokenVerifyView
from rest_framework.routers import DefaultRouter

app_name = 'api-v1-accounts'

# Router para ViewSets
router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('unidades', UnidadViewSet, basename='unidad')

urlpatterns = [
    # Autenticación JWT
    path('token/', LoginView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),
    path('logout/', LogoutView.as_view(), name='token_logout'),
    
    # Verificación y acceso
    path('verify-access/', VerifyAccessView.as_view(), name='verify_access'),
    path('quotation/', QuotationView.as_view(), name='quotation'),
] + router.urls
