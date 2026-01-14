"""Filters for Panorama SSOT app."""

import django_filters
from django.db.models import Q
from nautobot.apps.filters import NautobotFilterSet

from .models import SSOTPanoramaConfig


class SSOTPanoramaConfigFilterSet(NautobotFilterSet):
    """FilterSet for SSOTPanoramaConfig model."""

    q = django_filters.CharFilter(method="search", label="Search")

    class Meta:
        """Meta attributes for filter."""

        model = SSOTPanoramaConfig

        fields = "__all__"

    def search(self, queryset, _name, value):
        """String search of SSOTPanoramaConfig records."""
        if not value.strip():
            return queryset
        return queryset.filter(Q(name__icontains=value))  # pylint: disable=unsupported-binary-operation
