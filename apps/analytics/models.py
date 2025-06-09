from django.db import models
from django.db.models import JSONField
# Create your models here.

# Modelo para métricas de HubSpot Engagements
class HubspotEngagement(models.Model):
    id = models.CharField(primary_key=True, max_length=255)
    engagement_id = models.CharField(max_length=255)
    type = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(blank=True, null=True)
    owner_id = models.CharField(max_length=255, blank=True, null=True)
    team_id = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=255, blank=True, null=True)
    contact_ids = JSONField(blank=True, null=True)
    company_ids = JSONField(blank=True, null=True)
    deal_ids = JSONField(blank=True, null=True)
    last_sync_date = models.DateTimeField(blank=True, null=True)
    created_date = models.DateTimeField(blank=True, null=True)
    updated_date = models.DateTimeField(blank=True, null=True)
    body_preview = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.engagement_id

    class Meta:
        managed = False
        db_table = '"analytics"."hubspot_engagements"'
