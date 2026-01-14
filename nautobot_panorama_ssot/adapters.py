"""SSOT Adapter for Panorama integration."""
from typing import List, Optional
from nautobot_ssot.contrib import NautobotAdapter, NautobotModel
from diffsync import DiffSyncModel

try:
    from nautobot_firewall_models import models as firewall_models
except ImportError:
    firewall_models = None

#
# -------------------------
# DiffSync MODELS
# -------------------------
#

class PanoramaAddress(DiffSyncModel):
    """Represents a Panorama Address Object."""
    _modelname = "address_object"
    _identifiers = ("name",)
    _attributes = ("value", "description", "device_group")

    name: str
    value: Optional[str] = None
    description: Optional[str] = None
    device_group: Optional[str] = None

    @classmethod
    def create(cls, adapter, ids, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def update(self, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def delete(self):
        raise NotImplementedError("Panorama is read-only as a source adapter")


class PanoramaAddressGroup(DiffSyncModel):
    """Represents a Panorama Address Group."""
    _modelname = "address_group"
    _identifiers = ("name",)
    _attributes = ("static_members", "dynamic_filter", "description", "device_group")

    name: str
    static_members: Optional[List[str]] = None
    dynamic_filter: Optional[str] = None
    description: Optional[str] = None
    device_group: Optional[str] = None

    @classmethod
    def create(cls, adapter, ids, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def update(self, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def delete(self):
        raise NotImplementedError("Panorama is read-only as a source adapter")


class PanoramaService(DiffSyncModel):
    """Represents a Panorama Service Object."""
    _modelname = "service_object"
    _identifiers = ("name",)
    _attributes = ("port", "protocol", "description", "device_group")

    name: str
    port: Optional[str] = None
    protocol: Optional[str] = None
    description: Optional[str] = None
    device_group: Optional[str] = None

    @classmethod
    def create(cls, adapter, ids, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def update(self, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def delete(self):
        raise NotImplementedError("Panorama is read-only as a source adapter")


class PanoramaServiceGroup(DiffSyncModel):
    """Represents a Panorama Service Group."""
    _modelname = "service_group"
    _identifiers = ("name",)
    _attributes = ("service_members", "description", "device_group")

    name: str
    service_members: Optional[List[str]] = None
    description: Optional[str] = None
    device_group: Optional[str] = None

    @classmethod
    def create(cls, adapter, ids, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def update(self, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def delete(self):
        raise NotImplementedError("Panorama is read-only as a source adapter")


class PanoramaZone(DiffSyncModel):
    """Represents a Panorama Zone Object."""
    _modelname = "zone"
    _identifiers = ("name",)
    _attributes = ("description", "device_group")

    name: str
    description: Optional[str] = None
    device_group: Optional[str] = None

    @classmethod
    def create(cls, adapter, ids, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def update(self, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def delete(self):
        raise NotImplementedError("Panorama is read-only as a source adapter")


class PanoramaApplication(DiffSyncModel):
    """Represents a Panorama Application Object."""
    _modelname = "application_object"
    _identifiers = ("name",)
    _attributes = ("category", "subcategory", "technology", "risk", "description", "device_group")

    name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    technology: Optional[str] = None
    risk: Optional[int] = None
    description: Optional[str] = None
    device_group: Optional[str] = None

    @classmethod
    def create(cls, adapter, ids, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def update(self, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def delete(self):
        raise NotImplementedError("Panorama is read-only as a source adapter")


class PanoramaApplicationGroup(DiffSyncModel):
    """Represents a Panorama Application Group."""
    _modelname = "application_group"
    _identifiers = ("name",)
    _attributes = ("app_members", "description", "device_group")

    name: str
    app_members: Optional[List[str]] = None
    description: Optional[str] = None
    device_group: Optional[str] = None

    @classmethod
    def create(cls, adapter, ids, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def update(self, attrs):
        raise NotImplementedError("Panorama is read-only as a source adapter")

    def delete(self):
        raise NotImplementedError("Panorama is read-only as a source adapter")


#
# -------------------------
# Panorama Source Adapter
# -------------------------
#

class PanoramaSourceAdapter(NautobotAdapter):
    """Loads address, service, zone, and application objects from multiple Panorama Device Groups."""

    address_object = PanoramaAddress
    address_group = PanoramaAddressGroup
    service_object = PanoramaService
    service_group = PanoramaServiceGroup
    zone = PanoramaZone
    application_object = PanoramaApplication
    application_group = PanoramaApplicationGroup

    top_level = (
        "address_object",
        "address_group",
        "service_object",
        "service_group",
        "zone",
        "application_object",
        "application_group",
    )

    def __init__(self, client=None, device_groups=None, *args, **kwargs):
        """
        client: your Panorama API client
        device_groups: list of device-group names
        """
        super().__init__(*args, **kwargs)
        self.client = client
        self.device_groups = device_groups or []

    #
    # Loader ― Populate DiffSync models from Panorama
    #

    def load(self):
        """Load data from Panorama into the adapter."""
        for dg in self.device_groups:
            # -------------------------
            # Address Objects
            # -------------------------
            try:
                for obj in self.client.get_address_objects(dg):
                    self.add(PanoramaAddress(
                        name=obj["name"],
                        value=obj.get("value"),
                        description=obj.get("description"),
                        device_group=dg,
                    ))
            except Exception as exc:
                self.job.logger.warning(f"Failed to load address objects for {dg}: {exc}")

            # -------------------------
            # Address Groups
            # -------------------------
            try:
                for grp in self.client.get_address_groups(dg):
                    self.add(PanoramaAddressGroup(
                        name=grp["name"],
                        static_members=grp.get("static", []),
                        dynamic_filter=grp.get("dynamic"),
                        description=grp.get("description"),
                        device_group=dg,
                    ))
            except Exception as exc:
                self.job.logger.warning(f"Failed to load address groups for {dg}: {exc}")

            # -------------------------
            # Service Objects
            # -------------------------
            try:
                for svc in self.client.get_service_objects(dg):
                    self.add(PanoramaService(
                        name=svc["name"],
                        port=svc.get("port"),
                        protocol=svc.get("protocol"),
                        description=svc.get("description"),
                        device_group=dg,
                    ))
            except Exception as exc:
                self.job.logger.warning(f"Failed to load service objects for {dg}: {exc}")

            # -------------------------
            # Service Groups
            # -------------------------
            try:
                for svc_grp in self.client.get_service_groups(dg):
                    self.add(PanoramaServiceGroup(
                        name=svc_grp["name"],
                        service_members=svc_grp.get("members", []),
                        description=svc_grp.get("description"),
                        device_group=dg,
                    ))
            except Exception as exc:
                self.job.logger.warning(f"Failed to load service groups for {dg}: {exc}")

            # -------------------------
            # Zones
            # -------------------------
            try:
                for zone in self.client.get_zones(dg):
                    self.add(PanoramaZone(
                        name=zone["name"],
                        description=zone.get("description"),
                        device_group=dg,
                    ))
            except Exception as exc:
                self.job.logger.warning(f"Failed to load zones for {dg}: {exc}")

            # -------------------------
            # Application Objects
            # -------------------------
            try:
                for app in self.client.get_applications(dg):
                    self.add(PanoramaApplication(
                        name=app["name"],
                        category=app.get("category"),
                        subcategory=app.get("subcategory"),
                        technology=app.get("technology"),
                        risk=app.get("risk"),
                        default_type=app.get("default_type"),
                        default_ip_protocol=app.get("default_ip_protocol"),
                        description=app.get("description"),
                        device_group=dg,
                    ))
            except Exception as exc:
                self.job.logger.warning(f"Failed to load applications for {dg}: {exc}")

            # -------------------------
            # Application Groups
            # -------------------------
            try:
                for app_grp in self.client.get_application_groups(dg):
                    self.add(PanoramaApplicationGroup(
                        name=app_grp["name"],
                        app_members=app_grp.get("members", []),
                        description=app_grp.get("description"),
                        device_group=dg,
                    ))
            except Exception as exc:
                self.job.logger.warning(f"Failed to load application groups for {dg}: {exc}")

        # Count all loaded objects
        total_count = sum(len(self.get_all(model)) for model in self.top_level)
        self.job.logger.info(f"Loaded {total_count} total objects from Panorama")


#
# -------------------------
# Nautobot Firewall Models
# -------------------------
#

class NautobotAddress(NautobotModel):
    """DiffSync model for Nautobot AddressObject."""
    _model = firewall_models.AddressObject if firewall_models else None
    _modelname = "address_object"
    _identifiers = ("name",)

    name: str
    value: Optional[str] = None
    description: Optional[str] = None
    device_group: Optional[str] = None

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create AddressObject in Nautobot."""
        if not firewall_models:
            adapter.job.logger.warning("nautobot_firewall_models not installed")
            return None
        
        obj = firewall_models.AddressObject.objects.create(
            name=ids["name"],
            value=attrs.get("value"),
            description=attrs.get("description", ""),
        )
        adapter.job.logger.info(f"Created AddressObject: {obj.name}")
        return obj

    def update(self, attrs):
        """Update AddressObject in Nautobot."""
        obj = firewall_models.AddressObject.objects.get(name=self.name)
        if "value" in attrs:
            obj.value = attrs["value"]
        if "description" in attrs:
            obj.description = attrs["description"]
        obj.save()
        self.adapter.job.logger.info(f"Updated AddressObject: {obj.name}")
        return obj

    def delete(self):
        """Delete AddressObject from Nautobot."""
        obj = firewall_models.AddressObject.objects.get(name=self.name)
        obj.delete()
        self.adapter.job.logger.info(f"Deleted AddressObject: {self.name}")
        return self


class NautobotAddressGroup(NautobotModel):
    """DiffSync model for Nautobot AddressObjectGroup."""
    _model = firewall_models.AddressObjectGroup if firewall_models else None
    _modelname = "address_group"
    _identifiers = ("name",)

    name: str
    static_members: Optional[List[str]] = None
    dynamic_filter: Optional[str] = None
    description: Optional[str] = None
    device_group: Optional[str] = None


class NautobotService(NautobotModel):
    """DiffSync model for Nautobot ServiceObject."""
    _model = firewall_models.ServiceObject if firewall_models else None
    _modelname = "service_object"
    _identifiers = ("name",)

    name: str
    port: Optional[str] = None
    protocol: Optional[str] = None
    description: Optional[str] = None
    device_group: Optional[str] = None


class NautobotServiceGroup(NautobotModel):
    """DiffSync model for Nautobot ServiceObjectGroup."""
    _model = firewall_models.ServiceObjectGroup if firewall_models else None
    _modelname = "service_group"
    _identifiers = ("name",)

    name: str
    service_members: Optional[List[str]] = None
    description: Optional[str] = None
    device_group: Optional[str] = None


class NautobotZone(NautobotModel):
    """DiffSync model for Nautobot Zone."""
    _model = firewall_models.Zone if firewall_models else None
    _modelname = "zone"
    _identifiers = ("name",)

    name: str
    description: Optional[str] = None
    device_group: Optional[str] = None


class NautobotApplication(NautobotModel):
    """DiffSync model for Nautobot ApplicationObject."""
    _model = firewall_models.ApplicationObject if firewall_models else None
    _modelname = "application_object"
    _identifiers = ("name",)

    name: str
    category: Optional[str] = None
    subcategory: Optional[str] = None
    technology: Optional[str] = None
    risk: Optional[int] = None
    default_type: Optional[str] = None
    default_ip_protocol: Optional[str] = None
    description: Optional[str] = None
    device_group: Optional[str] = None


class NautobotApplicationGroup(NautobotModel):
    """DiffSync model for Nautobot ApplicationObjectGroup."""
    _model = firewall_models.ApplicationObjectGroup if firewall_models else None
    _modelname = "application_group"
    _identifiers = ("name",)

    name: str
    app_members: Optional[List[str]] = None
    description: Optional[str] = None
    device_group: Optional[str] = None


class NautobotTargetAdapter(NautobotAdapter):
    """Nautobot adapter for receiving Panorama data."""

    address_object = NautobotAddress
    address_group = NautobotAddressGroup
    service_object = NautobotService
    service_group = NautobotServiceGroup
    zone = NautobotZone
    application_object = NautobotApplication
    application_group = NautobotApplicationGroup

    top_level = (
        "address_object",
        "address_group",
        "service_object",
        "service_group",
        "zone",
        "application_object",
        "application_group",
    )
