from django.urls import path, include

urlpatterns = [
    path('v1/', include('api.v1.urls')),
    # En el futuro, cuando se necesite una nueva versión:
    # path('v2/', include('api.v2.urls')),
]
