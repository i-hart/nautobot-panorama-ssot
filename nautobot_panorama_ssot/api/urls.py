"""Django urlpatterns declaration for nautobot_ssot panorama API."""

from rest_framework import routers

from nautobot_panorama_ssot.api.views import SSOTPanoramaConfigView

router = routers.DefaultRouter()

router.register("SSOTPanoramaConfig", SSOTPanoramaConfigView)
app_name = "nautobot_panorama_ssot"  # pylint: disable=invalid-name

urlpatterns = router.urls
