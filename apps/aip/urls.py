from django.urls import path
from .views import UploadAIPXMLView

urlpatterns = [
    path('upload-xml/', UploadAIPXMLView.as_view(), name='aip-upload-xml'),
]
