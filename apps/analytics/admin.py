from django.contrib import admin

from .models import HubspotEngagement

@admin.register(HubspotEngagement)
class HubspotEngagementAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'engagement_id',
        'type',
        'created_at',
        'owner_id',
        'team_id',
        #'source',
        'contact_ids',
        'company_ids',
        'deal_ids',
        'last_sync_date',
        'created_date',
        'updated_date',
        #'body_preview'
    ]
    