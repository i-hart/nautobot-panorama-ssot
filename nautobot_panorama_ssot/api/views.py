"""API views for nautobot_ssot panorama."""

from nautobot.apps.api import NautobotModelViewSet

from nautobot_panorama_ssot.filters import SSOTPanoramaConfigFilterSet
from nautobot_panorama_ssot.models import SSOTPanoramaConfig

from .serializers import SSOTPanoramaConfigSerializer


class SSOTPanoramaConfigView(NautobotModelViewSet):  # pylint: disable=too-many-ancestors
    """API CRUD operations set for the SSOTPanoramaConfig view."""

    queryset = SSOTPanoramaConfig.objects.all()
    filterset_class = SSOTPanoramaConfigFilterSet
    serializer_class = SSOTPanoramaConfigSerializer
