"""SSOT Job for Panorama sync."""
from __future__ import annotations
from typing import Tuple

import logging

from nautobot.apps.jobs import (
    BooleanVar,
    ObjectVar,
    ChoiceVar,
    register_jobs,
)

from nautobot_firewall_models.models import LogicalGroup, ControlPlaneSystem
from nautobot.dcim.models import Controller
from nautobot.extras.models import ExternalIntegration
from nautobot.extras.choices import (
    SecretsGroupAccessTypeChoices,
    SecretsGroupSecretTypeChoices,
)
from nautobot_ssot.jobs import DataSource, DataTarget

from nautobot_panorama_ssot.diffsync.adapters.nautobot import NautobotAdapter
from nautobot_panorama_ssot.diffsync.adapters.panorama import PanoramaAdapter
from nautobot_panorama_ssot.utils.client import PanoramaClient

logger = logging.getLogger(__name__)

name = "SSoT - Palo Alto Panorama"

# ============================================================
# Shared Runtime Options
# ============================================================

class PanoramaJobMixin:

    control_plane = ObjectVar(
        model=ControlPlaneSystem,
        required=True,
        label="Control Plane System",
        description="Panorama instance mapped to this Control Plane System",
    )

    @property
    def selected_control_plane(self):
        return self.kwargs["control_plane"]

    forward_integration = ObjectVar(
        model=ExternalIntegration,
        required=False,
        label="Forward External Integration",
        description="Optional Forward integration for compliance and blast analysis",
    )

    @property
    def selected_forward_integration(self):
        return self.kwargs.get("forward_integration")

    simulation_mode = BooleanVar(default=False)
    drift_only = BooleanVar(default=False)
    change_window_only = BooleanVar(default=False)

    safe_commit_mode = ChoiceVar(
        choices=[
            ("disabled", "Disabled"),
            ("advisory", "Advisory"),
            ("enforced", "Enforced"),
        ],
        default="advisory",
    )

    require_approval = BooleanVar(default=False)
    enable_compliance_checks = BooleanVar(default=True)
    enable_blast_radius = BooleanVar(default=True)
    enable_risk_scoring = BooleanVar(default=True)
    enable_rule_optimizer = BooleanVar(default=True)

    # ========================================================
    # Credential Resolution
    # ========================================================

    def _get_creds_from_integration(

        self, ei: ExternalIntegration
    ) -> Tuple[str, str, bool, int]:

        if not ei.secrets_group:
            raise ValueError(f"ExternalIntegration '{ei}' has no SecretsGroup")

        sg = ei.secrets_group

        api_key = sg.get_secret_value(
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_TOKEN,
        )

        if not api_key:
            raise ValueError("API token not found in SecretsGroup")

        base_url = getattr(ei, "remote_url", None) or getattr(ei, "url", None)
        if not base_url:
            raise ValueError("ExternalIntegration missing remote_url")

        verify_ssl = bool(getattr(ei, "verify_ssl", True))
        timeout = int(getattr(ei, "timeout", 30))

        return base_url, api_key, verify_ssl, timeout

    # ========================================================
    # Adapter Builder
    # ========================================================

    def build_panorama_adapter(self):

        cp = self.kwargs["control_plane"]

        if not cp:
            raise ValueError("ControlPlaneSystem selection is required")

        ei = cp.external_integration

        if not ei:
            raise ValueError(f"ControlPlaneSystem '{cp}' has no ExternalIntegration")

        base_url, api_key, verify_ssl, timeout = self._get_creds_from_integration(ei)

        # Optional Forward
        forward_creds = None

        forward_ei = self.kwargs.get("forward_integration")
        if forward_ei:
            f_url, f_token, _, _ = \
                self._get_creds_from_integration(forward_ei)
    
            forward_creds = {
                "base_url": f_url,
                "token": f_token,
            }

        return PanoramaAdapter(
            control_plane=cp,
            base_url=base_url,
            api_key=api_key,
            verify_ssl=verify_ssl,
            timeout=timeout,
            forward_creds=forward_creds,
            logger=self.logger,
            simulation_mode=self.kwargs.get("simulation_mode", False),
            drift_only=self.kwargs.get("drift_only", False),
            change_window_only=self.kwargs.get("change_window_only", False),
            safe_commit_mode=self.kwargs.get("safe_commit_mode", "advisory"),
            require_approval=self.kwargs.get("require_approval", False),
            enable_compliance_checks=self.kwargs.get("enable_compliance_checks", True),
            enable_blast_radius=self.kwargs.get("enable_blast_radius", True),
            enable_risk_scoring=self.kwargs.get("enable_risk_scoring", True),
            enable_rule_optimizer=self.kwargs.get("enable_rule_optimizer", True),
        )

# ============================================================
# Panorama → Nautobot
# ============================================================

class PanoramaToNautobotSync(PanoramaJobMixin, DataSource, DataTarget):

    name = "Panorama ⟹  Nautobot Sync"
    description = "Authoritative Panorama → Nautobot synchronization"
    dryrun_default = False

    def run(self, *args, **kwargs):
        self.kwargs = kwargs
        return super().run(*args, **kwargs)

    def load_source_adapter(self):
        self.source_adapter = self.build_panorama_adapter()
        self.source_adapter.load()

    def load_target_adapter(self):
        self.target_adapter = NautobotAdapter(
            job=self,
        )
        self.target_adapter.load()


# ============================================================
# Nautobot → Panorama
# ============================================================

class NautobotToPanoramaSync(PanoramaJobMixin, DataSource, DataTarget):

    name = "Nautobot ⟹  Panorama Sync"
    description = "Authoritative Nautobot → Panorama synchronization"
    dryrun_default = False

    def run(self, *args, **kwargs):
        self.kwargs = kwargs
        return super().run(*args, **kwargs)

    def load_source_adapter(self):
        self.source_adapter = NautobotAdapter(
            job=self,
            sync=self,
        )
        self.source_adapter.load()

    def load_target_adapter(self):
        self.target_adapter = self.build_panorama_adapter()
        self.target_adapter.load()


# ============================================================
# Register
# ============================================================

register_jobs(
    PanoramaToNautobotSync,
    NautobotToPanoramaSync,
)
