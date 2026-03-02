"""Initialize Adapter classes for loading DiffSyncModels with data from Panorama or Nautobot."""

from .panorama import PanoramaAdapter
from .nautobot import NautobotAdapter

__all__ = [
    "PanoramaAdapter",
    "NautobotAdapter",
]
