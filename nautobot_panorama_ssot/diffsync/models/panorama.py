"""Nautobot SSoT Panorama DiffSync models for Nautobot SSoT Panorama SSoT."""

from nautobot_panorama_ssot.diffsync.models.base import (
    ControlPlaneModel,
    VirtualSystemModel,
    LogicalGroupModel,
    TagModel,
    AddressModel,
    AddressGroupModel,
    ServiceModel,
    ServiceGroupModel,
    ApplicationModel,
    ApplicationGroupModel,
    RuleModel,
)



class PanoramaControlPlane(ControlPlaneModel):
    """SolarWinds implementation of ControlPlane DiffSync Model."""
    
    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create ControlPlaneModel in Panorama from PanoramaControlPlane object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):
        """Update ControlPlaneModel in Panorama from PanoramaControlPlane object."""
        raise NotImplementedError

    def delete(self):
        """Delete ControlPlaneModel in Panorama from PanoramaControlPlane object."""
        raise NotImplementedError  

class PanoramaVirtualSystem(VirtualSystemModel):
    """SolarWinds implementation of VirtualSystem DiffSync Model."""

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create VirtualSystemModel in Panorama from PanoramaVirtualSystem object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):
        """Update VirtualSystemModel in Panorama from PanoramaVirtualSystem object."""
        raise NotImplementedError

    def delete(self):
        """Delete VirtualSystemModel in Panorama from PanoramaVirtualSystem object."""
        raise NotImplementedError

class PanoramaLogicalGroup(LogicalGroupModel):
    """SolarWinds implementation of LogicalGroup DiffSync Model."""
    
    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create LogicalGroupModel in Panorama from PanoramaLogicalGroup object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):    
        """Update LogicalGroupModel in Panorama from PanoramaLogicalGroup object."""
        raise NotImplementedError
    
    def delete(self):
        """Delete LogicalGroupModel in Panorama from PanoramaLogicalGroup object."""
        raise NotImplementedError

class PanoramaTag(TagModel):
    """SolarWinds implementation of Tag DiffSync Model."""

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create TagModel in Panorama from PanoramaTag object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):    
        """Update TagModel in Panorama from PanoramaTag object."""
        raise NotImplementedError

    def delete(self):
        """Delete TagModel in Panorama from PanoramaTag object."""
        raise NotImplementedError

class PanoramaAddress(AddressModel):
    """SolarWinds implementation of Address DiffSync Model."""

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create AddressModel in Panorama from PanoramaAddress object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):    
        """Update AddressModel in Panorama from PanoramaAddress object."""

    def delete(self):
        """Delete AddressModel in Panorama from PanoramaAddress object."""
        raise NotImplementedError

class PanoramaAddressGroup(AddressGroupModel):
    """SolarWinds implementation of AddressGroup DiffSync Model."""

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create AddressGroupModel in Panorama from PanoramaAddressGroup object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):    
        """Update AddressGroupModel in Panorama from PanoramaAddressGroup object."""

    def delete(self):
        """Delete AddressGroupModel in Panorama from PanoramaAddressGroup object."""
        raise NotImplementedError

class PanoramaService(ServiceModel):
    """SolarWinds implementation of Service DiffSync Model."""

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create ServiceModel in Panorama from PanoramaService object."""
        raise NotImplementedError
    
    def update(cls, adapter, ids, attr):    
        """Update ServiceModel in Panorama from PanoramaService object."""

    def delete(self):
        """Delete ServiceModel in Panorama from PanoramaService object."""
        raise NotImplementedError

class PanoramaServiceGroup(ServiceGroupModel):
    """SolarWinds implementation of ServiceGroup DiffSync Model."""

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create ServiceGroupModel in Panorama from PanoramaServiceGroup object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):    
        """Update ServiceGroupModel in Panorama from PanoramaServiceGroup object."""

    def delete(self):
        """Delete ServiceGroupModel in Panorama from PanoramaServiceGroup object."""
        raise NotImplementedError

class PanoramaApplication(ApplicationModel):
    """SolarWinds implementation of Application DiffSync Model."""

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create ApplicationModel in Panorama from PanoramaApplication object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):
        """Update ApplicationModel in Panorama from PanoramaApplication object."""

    def delete(self):
        """Delete ApplicationModel in Panorama from PanoramaApplication object."""
        raise NotImplementedError

class PanoramaApplicationGroup(ApplicationGroupModel):
    """SolarWinds implementation of ApplicationGroup DiffSync Model."""

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create ApplicationGroupModel in Panorama from PanoramaApplicationGroup object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):
        """Update ApplicationGroupModel in Panorama from PanoramaApplicationGroup object."""

    def delete(self):
        """Delete ApplicationGroupModel in Panorama from PanoramaApplicationGroup object."""
        raise NotImplementedError

class PanoramaRule(RuleModel):
    """SolarWinds implementation of Rule DiffSync Model."""

    @classmethod
    def create(cls, adapter, ids, attrs):
        """Create RuleModel in Panorama from PanoramaRule object."""
        raise NotImplementedError

    def update(cls, adapter, ids, attr):    
        """Update RuleModel in Panorama from PanoramaRule object."""

    def delete(self):
        """Delete RuleModel in Panorama from PanoramaRule object."""
        raise NotImplementedError
