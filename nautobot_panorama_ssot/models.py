"""Models for Nautobot Panorama SSOT App."""

from django.core.exceptions import ValidationError
from django.db import models

try:
    from nautobot.apps.constants import CHARFIELD_MAX_LENGTH
except ImportError:
    CHARFIELD_MAX_LENGTH = 255

from nautobot.apps.models import PrimaryModel
from nautobot.core.models.generics import OrganizationalModel

from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices
from nautobot.extras.models import SecretsGroupAssociation, ExternalIntegration

# class PanoramaConnection(PrimaryModel):
class SSOTPanoramaConfig(PrimaryModel):
    """Model to store Panorama connection details using External Integration."""
    

    name = models.CharField(max_length=CHARFIELD_MAX_LENGTH, unique=True)
    # TODO: Claify how saved views can be done for child apps
    is_saved_view_model = False
    description = models.CharField(
        max_length=CHARFIELD_MAX_LENGTH,
        blank=True,
    )

    panorama_instance = models.ForeignKey(
        to="extras.ExternalIntegration",
        on_delete=models.PROTECT,
        verbose_name="Panorama Instance",
        related_name="panorama_instance",
        help_text="Panorama Instance",
    )

    device_group = models.CharField(
        max_length=255,
        blank=True,
        help_text="Default Panorama Device Group to sync"
    )
    
    template = models.CharField(
        max_length=255,
        blank=True,
        help_text="Default Panorama Template to sync"
    )
    
    verify_ssl = models.BooleanField(
        default=True,
        help_text="Verify SSL certificates when connecting to Panorama"
    )

    enable_sync_to_nautobot = models.BooleanField(
        default=True,
        help_text="Enable syncing from Panorama to Nautobot"
    )
    
    job_enabled = models.BooleanField(
        default=True,
        help_text="Enable this config for use in jobs"
    )

    class Meta:
        """Meta class for SSOTPanoramaConfig."""

        verbose_name = "SSOT Panorama Config"
        verbose_name_plural = "SSOT Panorama Configs"

    def __str__(self):
        """String representation of singleton instance."""
        return self.name


    def _panorama_instance(self):
        """Performs validation of the panorama_instance field."""
        if not self.panorama_instance.secrets_group:
            raise ValidationError({"panorama_instance": "Panorama instance must have Secrets groups assigned."})
        try:
            self.panorama_instance.secrets_group.get_secret_value(
                access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
                secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME,
            )
        except SecretsGroupAssociation.DoesNotExist:
            raise ValidationError(  # pylint: disable=raise-missing-from
                {
                    "panorama_instance": "Secrets group for the Panorama instance must have secret with type Username and access type HTTP."
                }
            )
        try:
            self.panorama_instance.secrets_group.get_secret_value(
                access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
                secret_type=SecretsGroupSecretTypeChoices.TYPE_TOKEN,
            )
        except SecretsGroupAssociation.DoesNotExist:
            raise ValidationError(  # pylint: disable=raise-missing-from
                {
                    "panorama_instance": "Secrets group for the Panorama instance must have secret with type Password and access type TOKEN."
                }
            )


    def clean(self):
        """Clean method for PanoramaConnections."""
        super().clean()

        self._panorama_instance()


class PanoramaSyncLog(OrganizationalModel):
    """Log entries for Panorama sync operations."""
    
    connection = models.ForeignKey(
        to=SSOTPanoramaConfig,
        on_delete=models.CASCADE,
        related_name="sync_logs"
    )
    
    sync_start = models.DateTimeField(
        auto_now_add=True,
        help_text="When the sync started"
    )
    
    sync_end = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the sync completed"
    )
    
    status = models.CharField(
        max_length=50,
        choices=[
            ("running", "Running"),
            ("success", "Success"),
            ("failed", "Failed"),
            ("partial", "Partial Success"),
        ],
        default="running"
    )
    
    objects_created = models.IntegerField(default=0)
    objects_updated = models.IntegerField(default=0)
    objects_deleted = models.IntegerField(default=0)
    
    error_message = models.TextField(
        blank=True,
        help_text="Error details if sync failed"
    )
    
    class Meta:
        ordering = ["-sync_start"]
        verbose_name = "Panorama Sync Log"
        verbose_name_plural = "Panorama Sync Logs"
    
    def __str__(self):
        return f"{self.connection} - {self.sync_start} - {self.status}"
