"""Views implementation for SSOT Panorama."""

from nautobot.apps.ui import (
    Breadcrumbs,
    ModelBreadcrumbItem,
    ObjectDetailContent,
    ObjectFieldsPanel,
    ObjectTextPanel,
    SectionChoices,
    ViewNameBreadcrumbItem,
)
from nautobot.apps.views import (
    ObjectChangeLogViewMixin,
    ObjectDestroyViewMixin,
    ObjectDetailViewMixin,
    ObjectEditViewMixin,
    ObjectListViewMixin,
    ObjectNotesViewMixin,
)

from .api.serializers import SSOTPanoramaConfigSerializer
from .filters import SSOTPanoramaConfigFilterSet
from .forms import SSOTPanoramaConfigFilterForm, SSOTPanoramaConfigForm
from .models import SSOTPanoramaConfig
from .tables import SSOTPanoramaConfigTable


class SSOTPanoramaConfigUIViewSet(
    ObjectDestroyViewMixin,
    ObjectDetailViewMixin,
    ObjectListViewMixin,
    ObjectEditViewMixin,
    ObjectChangeLogViewMixin,
    ObjectNotesViewMixin,
):  # pylint: disable=abstract-method
    """SSOTPanoramaConfig UI ViewSet."""

    queryset = SSOTPanoramaConfig.objects.all()
    table_class = SSOTPanoramaConfigTable
    filterset_class = SSOTPanoramaConfigFilterSet
    filterset_form_class = SSOTPanoramaConfigFilterForm
    form_class = SSOTPanoramaConfigForm
    serializer_class = SSOTPanoramaConfigSerializer
    lookup_field = "pk"
    action_buttons = ("add",)

    breadcrumbs = Breadcrumbs(
        items={
            "list": [
                ViewNameBreadcrumbItem(view_name="plugins:nautobot_ssot:dashboard", label="Single Source of Truth"),
                ViewNameBreadcrumbItem(view_name="plugins:nautobot_ssot:config", label="SSOT Configs"),
                ModelBreadcrumbItem(model=SSOTPanoramaConfig),
            ],
            "detail": [
                ViewNameBreadcrumbItem(view_name="plugins:nautobot_ssot:dashboard", label="Single Source of Truth"),
                ViewNameBreadcrumbItem(view_name="plugins:nautobot_ssot:config", label="SSOT Configs"),
                ModelBreadcrumbItem(model=SSOTPanoramaConfig),
            ],
        }
    )
    object_detail_content = ObjectDetailContent(
        panels=[
            ObjectFieldsPanel(
                weight=100,
                section=SectionChoices.LEFT_HALF,
                fields=[
                    "name",
                    "description",
                    "panorama_instance",
                    "default_status",
                    "job_enabled",
                    "enable_sync_to_panorama",
                ],
            ),
        ]
    )
