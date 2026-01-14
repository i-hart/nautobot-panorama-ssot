"""Forms for Panorama SSOT app."""
from django import forms
from nautobot.apps.forms import NautobotModelForm, NautobotFilterForm
from nautobot.extras.models import ExternalIntegration

from .models import SSOTPanoramaConfig


class SSOTPanoramaConfigForm(NautobotModelForm):  # pylint: disable=too-many-ancestors
    """SSOTInfobloxConfig creation/edit form."""

    model = SSOTPanoramaConfig

    class Meta:
        """Meta attributes for the SSOTPanoramaConfigForm class."""

        model = SSOTPanoramaConfig
        fields = "__all__"


class SSOTPanoramaConfigFilterForm(NautobotFilterForm):  # pylint: disable=too-many-ancestors
    """Filter form for SSOTPanoramaConfig filter searches."""

    model = SSOTPanoramaConfig

    class Meta:
        """Meta attributes for the SSOTPanoramaConfigFilterForm class."""

        model = SSOTPanoramaConfig
        fields = "__all__"
