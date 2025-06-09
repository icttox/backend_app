from rest_framework import serializers
from .models import HubspotEngagement

class HubspotEngagementSerializer(serializers.ModelSerializer):
    class Meta:
        model = HubspotEngagement
        fields = '__all__'
