"""Signals for Panorama SSOT app."""
# Import signals if needed in the future
# This file is imported in __init__.py ready() method
# pylint: disable=duplicate-code

from django.conf import settings
from nautobot.core.signals import nautobot_database_ready
from nautobot.extras.choices import (
    CustomFieldTypeChoices,
    RelationshipTypeChoices,
    SecretsGroupAccessTypeChoices,
    SecretsGroupSecretTypeChoices,
)

from nautobot_panorama_ssot.constant import TAG_COLOR

#config = settings.PLUGINS_CONFIG["nautobot_panorama_ssot"]
config = settings.PLUGINS_CONFIG.get("nautobot_panorama_ssot", {})


def register_signals(sender):
    """Register signals for Panorama integration."""
    nautobot_database_ready.connect(nautobot_database_ready_callback, sender=sender)


def nautobot_database_ready_callback(sender, *, apps, **kwargs):  # pylint: disable=unused-argument,too-many-locals,too-many-statements
    """Create Tag and CustomField to note System of Record for SSoT.

    Callback function triggered by the nautobot_database_ready signal when the Nautobot database is fully ready.
    """
    # pylint: disable=invalid-name
    ContentType = apps.get_model("contenttypes", "ContentType")
    CustomField = apps.get_model("extras", "CustomField")
    Tag = apps.get_model("extras", "Tag")
    Relationship = apps.get_model("extras", "Relationship")
    ExternalIntegration = apps.get_model("extras", "ExternalIntegration")
    Secret = apps.get_model("extras", "Secret")
    SecretsGroup = apps.get_model("extras", "SecretsGroup")
    SecretsGroupAssociation = apps.get_model("extras", "SecretsGroupAssociation")
    Status = apps.get_model("extras", "Status")
    SSOTPanoramaConfig = apps.get_model("nautobot_panorama_ssot", "SSOTPanoramaConfig")

    tag_sync_from_panorama, _ = Tag.objects.get_or_create(
        name="SSoT Synced from Panorama",
        defaults={
            "name": "SSoT Synced from Panorama",
            "description": "Object synced at some point from Panorama",
            "color": TAG_COLOR,
        },
    )

    # Migrate existing configuration to a configuration object
    if not SSOTPanoramaConfig.objects.exists():
        # Get or create default status
        default_status_name = str(config.get("panorama_default_status", "Active"))
        found_status = Status.objects.filter(name=default_status_name)
        if found_status.exists():
            default_status = found_status.first()
        else:
            # Try to get "Active" status as fallback
            default_status = Status.objects.filter(name="Active").first()
            if not default_status:
                # Create a default status if none exists
                default_status, _ = Status.objects.get_or_create(
                    name="PanoramaDevStaging",
                    defaults={
                        "description": "Default status for Panorama SSOT",
                    }
                )

        try:
            panorama_request_timeout = int(config.get("panorama_request_timeout", 60))
        except (ValueError, TypeError):
            panorama_request_timeout = 60

        secrets_group, created = SecretsGroup.objects.get_or_create(
            name="PanoramaSSOTDefaultSecretGroup",
            defaults={
                "description": "Default secrets group for Panorama SSOT integration",
            }
        )

        if created:
            print(f"Created SecretsGroup: {secrets_group.name}")


        panorama_username, created = Secret.objects.get_or_create(
            name="Panorama Username - Default",
            defaults={
                "provider": "environment-variable",
                "parameters": {"variable": "NAUTOBOT_PANORAMA_SSOT_USERNAME"},
                "description": "Default Panorama username from environment variable",
            },
        )

        if created:
            print(f"Created Secret: {panorama_username.name}")


        panorama_token, created = Secret.objects.get_or_create(
            name="Panorama Token - Default",
            defaults={
                "provider": "environment-variable",
                "parameters": {"variable": "NAUTOBOT_PANORAMA_SSOT_PASSWORD"},
                "description": "Default Panorama API token from environment variable",
            },
        )

        if created:
            print(f"Created Secret: {panorama_token.name}")

        username_assoc, created = SecretsGroupAssociation.objects.get_or_create(
            secrets_group=secrets_group,
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_USERNAME,
            defaults={
                "secret": panorama_username,
            },
        )

        if created:
            print(f"Associated username secret with secrets group")


        token_assoc, created = SecretsGroupAssociation.objects.get_or_create(
            secrets_group=secrets_group,
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_TOKEN,
            defaults={
                "secret": panorama_token,
            },
        )

        if created:
            print(f"Associated token secret with secrets group")

        external_integration, created = ExternalIntegration.objects.get_or_create(
            name="DefaultPanoramaInstance",
            defaults={
                "remote_url": str(config.get("panorama_url", "https://panorama.replace.me.local")),
                "secrets_group": secrets_group,
                "verify_ssl": bool(config.get("panorama_verify_ssl", True)),
                "timeout": panorama_request_timeout,
                "extra_config": {},
            },
        )

        if created:
            print(f"Created ExternalIntegration: {external_integration.name}")
        else:
            # Update existing external integration with secrets group if not set
            if not external_integration.secrets_group:
                external_integration.secrets_group = secrets_group
                external_integration.save()
                print(f"Updated ExternalIntegration {external_integration.name} with secrets group")

        panorama_config, created = SSOTPanoramaConfig.objects.get_or_create(
            name="PanoramaConfigDefault",
            defaults={
                "description": "Auto-generated default configuration for Panorama SSOT",
                "panorama_instance": external_integration,
                "device_group": str(config.get("panorama_device_group", "shared")),
                "template": str(config.get("panorama_template", "default")),
                "verify_ssl": bool(config.get("panorama_verify_ssl", True)),
            },
        )
        
        if created:
            print(f"Created SSOTPanoramaConfig: {panorama_config.name}")
            print("\n" + "=" * 80)
            print("Panorama SSOT Default Configuration Created!")
            print("=" * 80)
            print(f"Config Name: {panorama_config.name}")
            print(f"Panorama URL: {external_integration.remote_url}")
            print(f"Device Group: {panorama_config.device_group}")
            print(f"Template: {panorama_config.template}")
            print("\nIMPORTANT: Set these environment variables:")
            print("  - NAUTOBOT_PANORAMA_SSOT_USERNAME")
            print("  - NAUTOBOT_PANORAMA_SSOT_TOKEN")
            print("\nOr update the secrets manually in the UI:")
            print(f"  Admin > Secrets > Edit '{panorama_username.name}'")
            print(f"  Admin > Secrets > Edit '{panorama_token.name}'")
            print("=" * 80 + "\n")
