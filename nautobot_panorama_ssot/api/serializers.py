"""API serializers for nautobot_ssot panorama."""

from nautobot.apps.api import NautobotModelSerializer

from nautobot_panorama_ssot.models import SSOTPanoramaConfig


class SSOTPanoramaConfigSerializer(NautobotModelSerializer):  # pylint: disable=too-many-ancestors
    """REST API serializer for SSOTPanoramaConfig records."""

    class Meta:
        """Meta attributes."""

        model = SSOTPanoramaConfig
        fields = "__all__"
