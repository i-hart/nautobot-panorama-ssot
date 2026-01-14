"""Django admin configuration."""
from django.contrib import admin
from nautobot.apps.admin import NautobotModelAdmin

from .models import SSOTPanoramaConfig

@admin.register(SSOTPanoramaConfig)
class SSOTPanoramaConfigAdmin(NautobotModelAdmin):
    """Admin for PanoramaConnection model."""
    
    list_display = [
        "pk",
        "panorama_instance",
        "device_group",
        "template",
        "verify_ssl",
    ]
    
    list_filter = ["verify_ssl"]
    
    search_fields = ["panorama_instance__name", "device_group", "template"]
