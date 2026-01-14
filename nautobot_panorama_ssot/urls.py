"""URL patterns for Panorama SSOT app."""
from django.urls import path
from nautobot.apps.urls import NautobotUIViewSetRouter

from . import views

app_name = "nautobot_panorama_ssot"

router = NautobotUIViewSetRouter()
router.register("SSOTPanoramaConfig", views.SSOTPanoramaConfigUIViewSet)
#router.register("sync-logs", views.PanoramaSyncLogUIViewSet)

urlpatterns = []

urlpatterns += router.urls
