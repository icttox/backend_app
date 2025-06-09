from rest_framework.routers import DefaultRouter
from django.urls import path, include
from .views import HubspotEngagementViewSet

router = DefaultRouter()
router.register('engagements', HubspotEngagementViewSet, basename='hubspotengagement')

urlpatterns = [
    path('', include(router.urls)),
]
