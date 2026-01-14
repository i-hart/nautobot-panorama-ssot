"""SSOT Job for Panorama sync."""
from __future__ import annotations

import logging
from typing import List

from django.templatetags.static import static
from nautobot.apps.jobs import Job, ObjectVar, BooleanVar, register_jobs
from nautobot.extras.models import ExternalIntegration
from nautobot.extras.choices import (
    SecretsGroupAccessTypeChoices,
    SecretsGroupSecretTypeChoices,
)

from nautobot_panorama_ssot.models import SSOTPanoramaConfig
from nautobot_panorama_ssot.adapters import PanoramaSourceAdapter, NautobotTargetAdapter
from nautobot_panorama_ssot.utils import PanoramaClient
from nautobot_ssot.jobs import DataSource


logger = logging.getLogger(__name__)

name = "Panorama SSOT"


class PanoramaSSOTJob(DataSource, Job):
    """Panorama → Nautobot SSoT Sync Job."""

    debug = BooleanVar(description="Enable debug (XML logging in Panorama client)")
    dryrun = BooleanVar(description="Dry-run mode (no DB writes)")

    # Internal plugin config option
    config = ObjectVar(
        model=SSOTPanoramaConfig,
        required=False,
        label="SSOT Panorama Config (optional)",
        query_params={"job_enabled": True},
    )

    # Raw ExternalIntegration fallback option
    external_integration = ObjectVar(
        model=ExternalIntegration,
        required=False,
        label="External Integration (Panorama)",
    )

    class Meta:
        name = "Panorama → Nautobot Sync"
        description = "Sync address objects, services, zones, and policies from Panorama into Nautobot."
        data_source = "Panorama"
        data_source_icon = static("nautobot_panorama_ssot/paloalto_logo.png")

    @classmethod
    def data_mappings(cls):
        return (
            "Address Objects: Panorama → nautobot_firewall_models.AddressObject",
            "Service Objects: Panorama → nautobot_firewall_models.ServiceObject",
            "Zones: Panorama → nautobot_firewall_models.Zone",
            "Policies: Panorama → nautobot_firewall_models.Policy",
            "Policy Rules: Panorama → nautobot_firewall_models.PolicyRule",
        )

    def _get_integration(self, config_instance, ext_integration) -> ExternalIntegration:
        """Return the ExternalIntegration instance to use."""
        # Use the actual runtime values, not the ObjectVar definitions
        if config_instance:
            return config_instance.panorama_instance

        if ext_integration:
            return ext_integration

        raise ValueError("No SSOT config or External Integration defined.")

    def _get_creds_from_integration(self, ei: ExternalIntegration):
        """Return (url, api_key, username, password, verify_ssl, timeout)."""
        sg = ei.secrets_group
        if not sg:
            raise ValueError(f"Integration {ei} has no SecretsGroup associated")

        def _safe_get(access, stype):
            try:
                return sg.get_secret_value(access_type=access, secret_type=stype)
            except Exception:
                return None

        api_key = _safe_get(
            SecretsGroupAccessTypeChoices.TYPE_HTTP,
            SecretsGroupSecretTypeChoices.TYPE_TOKEN,
        )
        username = _safe_get(
            SecretsGroupAccessTypeChoices.TYPE_HTTP,
            SecretsGroupSecretTypeChoices.TYPE_USERNAME,
        )
        password = _safe_get(
            SecretsGroupAccessTypeChoices.TYPE_HTTP,
            SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
        )

        base_url = getattr(ei, "remote_url", None) or getattr(ei, "url", None)
        if not base_url:
            raise ValueError("ExternalIntegration is missing `remote_url`.")

        verify_ssl = bool(getattr(ei, "verify_ssl", True))
        timeout = int(getattr(ei, "timeout", 30))

        return base_url, api_key, username, password, verify_ssl, timeout

    def load_source_adapter(self):
        """Load data from Panorama into the source adapter."""
        # Get job parameters
        config = self.kwargs.get("config")
        external_integration = self.kwargs.get("external_integration")
        debug = self.kwargs.get("debug", False)
        
        # Integration & Credentials
        try:
            ei = self._get_integration(config, external_integration)
        except Exception as exc:
            self.logger.error(f"Failed to select integration: {exc}")
            raise

        try:
            base_url, api_key, username, password, verify_ssl, timeout = \
                self._get_creds_from_integration(ei)
        except Exception as exc:
            self.logger.error(f"Failed to extract credentials: {exc}")
            raise

        # Build Panorama client
        try:
            client = PanoramaClient(
                base_url=base_url,
                api_key=api_key,
                username=username,
                password=password,
                verify_ssl=verify_ssl,
                timeout=timeout,
                log_xml=debug,
                logger_=self.logger,
            )
        except Exception as exc:
            self.logger.error(f"Failed to initialize Panorama client: {exc}")
            raise

        # Device Groups
        if config and config.device_group:
            device_groups = [
                dg.strip() for dg in config.device_group.split(",") if dg.strip()
            ]
        else:
            try:
                device_groups = client.get_device_groups()
            except Exception:
                device_groups = ["shared"]

        self.logger.info(f"Using device-groups: {device_groups}")

        # Create and load source adapter
        self.source_adapter = PanoramaSourceAdapter(
            job=self,
            sync=self.sync,
            client=client,
            device_groups=device_groups,
        )
        
        self.source_adapter.load()

    def load_target_adapter(self):
        """Load data from Nautobot into the target adapter."""
        self.target_adapter = NautobotTargetAdapter(job=self, sync=self.sync)
        self.target_adapter.load()

    def run(self, dryrun: bool = True, debug: bool = False, config=None, external_integration=None, **kwargs):
        """Execute the Panorama → Nautobot sync."""
        # Store kwargs for use in load_source_adapter
        self.kwargs = {
            "dryrun": dryrun,
            "debug": debug,
            "config": config,
            "external_integration": external_integration,
            **kwargs
        }
        
        # Call parent run method which handles the sync workflow
        super().run(dryrun=dryrun, **kwargs)


register_jobs(PanoramaSSOTJob)
