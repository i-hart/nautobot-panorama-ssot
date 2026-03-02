"""DiffSyncModel subclasses for Nautobot-to-Panorama data sync."""
from diffsync import DiffSyncModel
from typing import Optional, List


# ============================================================
# CONTROL PLANE
# ============================================================

class ControlPlaneModel(DiffSyncModel):
    _modelname = "control_plane"
    _identifiers = ("name",)
    _attributes = ("description",)

    name: str
    description: Optional[str] = None

    virtual_systems: List["VirtualSystemModel"] = None


# ============================================================
# VIRTUAL SYSTEM (vsys)
# ============================================================

class VirtualSystemModel(DiffSyncModel):
    _modelname = "virtual_system"
    _identifiers = ("name", "control_plane",)
    _attributes = ("description",)

    name: str
    control_plane: str
    description: Optional[str] = None

    logical_groups: List["LogicalGroupModel"] = None


# ============================================================
# LOGICAL GROUP (device_group abstraction)
# ============================================================

class LogicalGroupModel(DiffSyncModel):
    _modelname = "logical_group"
    _identifiers = ("name", "virtual_system", "scope")
    _attributes = ("description",)

    name: str
    virtual_system: str
    description: Optional[str] = None
    scope: str  # "shared" or "device-group"

    addresses: List["AddressModel"] = None
    address_groups: List["AddressGroupModel"] = None
    services: List["ServiceModel"] = None
    service_groups: List["ServiceGroupModel"] = None
    rules: List["RuleModel"] = None
    tags: List["TagModel"] = None


# ============================================================
# TAG
# ============================================================

class TagModel(DiffSyncModel):
    _modelname = "tag"
    _identifiers = ("name", "logical_group", "scope")
    _attributes = ("color",)

    name: str
    logical_group: str
    color: Optional[str] = None
    scope: str  # "shared" or "device-group"

# ============================================================
# ADDRESS OBJECT
# ============================================================

class AddressModel(DiffSyncModel):
    _modelname = "address"
    _identifiers = ("name", "logical_group", "scope")
    _attributes = ("value", "type", "description", "tags")

    name: str
    logical_group: str

    value: str
    type: str  # ip-netmask, ip-range, fqdn
    description: Optional[str] = None
    tags: List[str] = []
    scope: str  # "shared" or "device-group"

# ============================================================
# ADDRESS GROUP
# ============================================================

class AddressGroupModel(DiffSyncModel):
    _modelname = "address_group"
    _identifiers = ("name", "logical_group", "scope")
    _attributes = ("members", "dynamic_filter", "description", "tags")

    name: str
    logical_group: str

    members: List[str] = []
    dynamic_filter: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []
    scope: str  # "shared" or "device-group"

# ============================================================
# SERVICE
# ============================================================

class ServiceModel(DiffSyncModel):
    _modelname = "service"
    _identifiers = ("name", "logical_group", "scope")
    _attributes = ("protocol", "destination_port", "description", "tags")

    name: str
    logical_group: str

    protocol: str
    destination_port: str
    description: Optional[str] = None
    tags: List[str] = []
    scope: str  # "shared" or "device-group"

# ============================================================
# SERVICE GROUP
# ============================================================

class ServiceGroupModel(DiffSyncModel):
    _modelname = "service_group"
    _identifiers = ("name", "logical_group", "scope")
    _attributes = ("members", "description", "tags")

    name: str
    logical_group: str

    members: List[str] = []
    description: Optional[str] = None
    tags: List[str] = []
    scope: str  # "shared" or "device-group"

# ============================================================
# APPLICATION
# ============================================================

class ApplicationModel(DiffSyncModel):
    """Application Object model for Panorama"""

    _modelname = "application"
    _identifiers = ("name", "logical_group", "scope")
    _attributes = ("category", "subcategory", "technology", "risk", "description", "tags")

    name: str
    logical_group: str
    scope: str  # "shared" or "device-group"

    category: str
    subcategory: str
    technology: str
    risk: int
    description: Optional[str] = None
    tags: List[str] = []

# ============================================================
# APPLICATION-GROUP
# ============================================================

class ApplicationGroupModel(DiffSyncModel):
    _modelname = "application_group"
    _identifiers = ("name", "logical_group", "scope")
    _attributes = ("members", "description", "tags")

    name: str
    logical_group: str
    scope: str  # "shared" or "device-group"

    members: List[str] = []
    description: Optional[str] = None
    tags: List[str] = []


# ============================================================
# SECURITY RULE
# ============================================================

class RuleModel(DiffSyncModel):
    _modelname = "rule"
    _identifiers = ("name", "logical_group", "rulebase", "scope")
    _attributes = (
        "description",
        "source_zones",
        "destination_zones",
        "sources",
        "destinations",
        "services",
        "action",
        "disabled",
        "position",
        "tags",
    )

    name: str
    logical_group: str
    rulebase: str  # "pre" or "post"

    description: Optional[str] = None
    source_zones: List[str] = []
    destination_zones: List[str] = []
    sources: List[str] = []
    destinations: List[str] = []
    services: List[str] = []
    action: str = "allow"
    disabled: bool = False
    position: int = 0
    tags: List[str] = []
    scope: str  # "shared" or "device-group"

# ============================================================
# NAT RULE
# ============================================================

class NatRuleModel(DiffSyncModel):
    _modelname = "nat_rule"

    _identifiers = ("name", "device_group", "rulebase", "scope")

    _attributes = (
        "description",
        "from_zones",
        "to_zones",
        "sources",
        "destinations",
        "services",
        "source_translation",
        "destination_translation",
        "disabled",
        "position",
        "tags",
    )


    # -----------------------------
    # Identifiers
    # -----------------------------

    name: str
    device_group: str        # DG name or "shared"
    rulebase: str            # "pre" | "post"
    scope: str               # "shared" | "device-group"

    # -----------------------------
    # Attributes
    # -----------------------------

    description: Optional[str] = None

    from_zones: List[str] = []
    to_zones: List[str] = []

    sources: List[str] = []
    destinations: List[str] = []
    services: List[str] = []

    source_translation: Optional[str] = None
    destination_translation: Optional[str] = None

    disabled: bool = False
    position: Optional[int] = None
    tags: List[str] = []
