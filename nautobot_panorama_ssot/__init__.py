"""Nautobot Panorama SSOT App."""
from nautobot.apps import NautobotAppConfig


class SSOTPanoramaConfig(NautobotAppConfig):
    """App configuration for nautobot_panorama_ssot."""
    
    name = "nautobot_panorama_ssot"
    verbose_name = "Panorama SSOT"
    version = "3.0.0"
    author = "James Harting"
    description = "Nautobot SSoT integration for Palo Alto Panorama"
    base_url = "panorama-ssot"
    required_settings = []
    min_version = "3.0.0"
    max_version = "3.99.99"
    default_settings = {}
    
    def ready(self):
        """Register app when ready."""
        super().ready()

        # Import and register signals
        from nautobot_panorama_ssot import signals  # noqa: F401
        signals.register_signals(self)


config = SSOTPanoramaConfig
#config = PanoramaSSOTAppConfig
