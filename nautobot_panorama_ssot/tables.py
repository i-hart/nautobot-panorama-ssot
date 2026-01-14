"""Tables for Panorama SSOT app."""
import django_tables2 as tables
from nautobot.apps.tables import BaseTable, BooleanColumn, ButtonsColumn

from .models import SSOTPanoramaConfig


class SSOTPanoramaConfigTable(BaseTable):
    """Table for SSOTPanoramaConfig."""
    
    pk = tables.CheckBoxColumn()
    name = tables.LinkColumn()
    panorama_url = tables.Column(accessor="panorama_instance__remote_url")
    enable_sync_to_nautobot = BooleanColumn(orderable=False)
    job_enabled = BooleanColumn(orderable=False)    
    actions = ButtonsColumn(SSOTPanoramaConfig, buttons=("changelog", "edit", "delete"))    
    
#    external_integration = tables.Column(linkify=True)
    
    class Meta(BaseTable.Meta):
        """Meta attributes."""

        model = SSOTPanoramaConfig
        fields = (  # pylint: disable=nb-use-fields-all
            "pk",
            "name",
            "panorama_url",
            "enable_sync_to_nautobot",
            "device_group",
            "template",
            "verify_ssl",
            "job_enabled",
            "actions",
        )
