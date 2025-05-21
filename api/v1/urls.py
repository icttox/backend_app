from django.urls import path, include
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions

class APIv1Root(APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request, format=None):
        return Response({
            'accounts': '/api/v1/accounts/',
            'cotizador': '/api/v1/cotizador/',
            'endpoints': {
                'auth': {
                    'login': '/api/v1/accounts/token/',
                    'refresh': '/api/v1/accounts/token/refresh/',
                    'verify': '/api/v1/accounts/token/verify/',
                },
                'cotizaciones': '/api/v1/cotizador/cotizaciones/'
            }
        })

urlpatterns = [
    path('', APIv1Root.as_view(), name='api-v1-root'),
    path('accounts/', include('api.v1.accounts.urls')),
    path('cotizador/', include('api.v1.cotizador.urls')),
]
