# diffsync/adapters/nautobot.py

import logging
from django.db import transaction
from django.db.models import F
from django.contrib.contenttypes.models import ContentType

from diffsync import DiffSync
from diffsync.exceptions import ObjectNotFound

from nautobot.extras.models import Tag
from nautobot_firewall_models.models import (
    ControlPlaneSystem,
    LogicalGroup,
    AddressObject,
    AddressObjectGroup,
    ServiceObject,
    ServiceObjectGroup,
    ApplicationObject,
    ApplicationObjectGroup,
    PolicyRule,
    NATPolicy,
    NATPolicyRule,
)

from nautobot_panorama_ssot.constant import DEFAULT_ALLOW_DELETE, TAG_COLOR
from nautobot_panorama_ssot.diffsync.models.base import *

logger = logging.getLogger(__name__)


class NautobotAdapter(DiffSync):
    """
    Pure DiffSync Nautobot Adapter
    Enterprise-grade:
        - deterministic rule ordering
        - tag diff detection
        - bulk create optimization
        - safe deletes
        - transactional safety
    """

    control_plane = ControlPlaneModel
    logical_group = LogicalGroupModel
    address = AddressModel
    address_group = AddressGroupModel
    service = ServiceModel
    service_group = ServiceGroupModel
    application = ApplicationModel
    application_group = ApplicationGroupModel
    rule = RuleModel
    nat_rule = NatRuleModel
    tag = TagModel

    top_level = ["control_plane"]

    def __init__(self, job=None):
        super().__init__()
        self.job = job

    # ============================================================
    # LOAD
    # ============================================================

    def load(self):

        for cp in ControlPlaneSystem.objects.all():

            cp_model = self.control_plane(
                name=cp.name,
                description=cp.description,
            )
            self.add(cp_model)

            for lg in LogicalGroup.objects.filter(control_plane=cp):

                lg_model = self.logical_group(name=lg.name)
                self.add(lg_model)
                cp_model.add_child(lg_model)

                # Addresses
                for obj in AddressObject.objects.filter(logical_group=lg):
                    self.add(self.address(
                        name=obj.name,
                        logical_group=lg.name,
                        value=obj.value,
                        address_type=obj.address_type,
                        description=obj.description or "",
                        tags=list(obj.tags.values_list("name", flat=True)),
                    ))
                # Address Groups
                for obj in AddressObjectGroup.objects.filter(logical_group=lg).prefetch_related("members", "tags"):
                    self.add(
                        self.address_group(
                            name=obj.name,
                            logical_group=obj.logical_group.name,
                            description=obj.description,
                            members=[m.name for m in obj.members.all()],
                            tags=[t.name for t in obj.tags.all()],
                        )
                    )
                # Services
                for obj in ServiceObject.objects.filter(logical_group=lg):
                    self.add(self.service(
                        name=obj.name,
                        logical_group=lg.name,
                        protocol=obj.protocol,
                        port=obj.port,
                        description=obj.description or "",
                        tags=list(obj.tags.values_list("name", flat=True)),
                    ))
                # Service Groups
                for obj in ServiceObjectGroup.objects.filter(logical_group=lg).prefetch_related("members", "tags"):
                
                    self.add(
                        self.service_group(
                            name=obj.name,
                            logical_group=obj.logical_group.name,
                            description=obj.description,
                            members=[m.name for m in obj.members.all()],
                            tags=[t.name for t in obj.tags.all()],
                        )
                    )
                # Applications
                for obj in ApplicationObject.objects.filter(logical_group=lg):
                    self.add(self.application(
                        name=obj.name,
                        logical_group=lg.name,
                        description=obj.description,
                        tags=[t.name for t in obj.tags.all()],
                        )
                    )
                # Application Groups
                for obj in ApplicationObjectGroup.objects.filter(logical_group=lg).prefetch_related("members", "tags"):
                
                    self.add(
                        self.application_group(
                            name=obj.name,
                            logical_group=obj.logical_group.name,
                            description=obj.description,
                            members=[m.name for m in obj.members.all()],
                            tags=[t.name for t in obj.tags.all()],
                        )
                    )
                # Rules
                for rule in PolicyRule.objects.filter(
                        logical_group=lg
                ).order_by("index"):

                    self.add(self.rule(
                        name=rule.name,
                        logical_group=lg.name,
                        rulebase=rule.rulebase,
                        index=rule.index,
                        action=rule.action,
                        description=rule.description or "",
                        tags=list(rule.tags.values_list("name", flat=True)),
                    ))
                # NAT Rules
                for nat in NatPolicyRule.objects.filter(
                        policy__logical_group=lg
                ).order_by("index"):
                
                    self.add(self.nat_rule(
                        name=nat.name,
                        logical_group=lg.name,
                        index=nat.index,
                        destination_zone=nat.destination_zone,
                        source_zone=nat.source_zone,
                        remark=nat.remark or "",
                        log=nat.log,
                        status=nat.status,
                        original_source_addresses=[o.name for o in nat.original_source_addresses.all()],
                        original_destination_addresses=[o.name for o in nat.original_destination_addresses.all()],
                        translated_source_addresses=[o.name for o in nat.translated_source_addresses.all()],
                        translated_destination_addresses=[o.name for o in nat.translated_destination_addresses.all()],
                    ))

    # ============================================================
    # TAG ENGINE
    # ============================================================
    def apply_tags(self, instance, tag_names, prefix=None, control_plane=None):

        tag_names = tag_names or []

        if prefix:
            tag_names = [f"{prefix}-{t}" for t in tag_names]

        if control_plane:
            tag_names = [f"{control_plane}-{t}" for t in tag_names]

        desired = set(tag_names)
        existing = set(instance.tags.values_list("name", flat=True))

        if desired == existing:
            return False

        tag_objs = []
        for name in desired:
            tag, _ = Tag.objects.get_or_create(
                name=name,
                defaults={"color": TAG_COLOR},
            )
            tag_objs.append(tag)

        instance.tags.set(tag_objs)
        return True

    # ============================================================
    # CRUD CORE
    # ============================================================
    def _get_lg(self, model):
        return LogicalGroup.objects.get(name=model.logical_group)
    

    # ============================================================
    # ADDRESS CRUD
    # ============================================================
    @transaction.atomic
    def create_address(self, model):

        lg = LogicalGroup.objects.get(name=model.logical_group)

        obj = AddressObject.objects.create(
            name=model.name,
            logical_group=LogicalGroup.objects.get(name=model.logical_group),
            value=model.value,
            address_type=model.address_type,
            description=model.description,
        )

        self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def update_address(self, model, diffs):

        obj = AddressObject.objects.get(name=model.name)

        for field, change in diffs.items():
            setattr(obj, field, change["new"])

        obj.validated_save()
        self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def delete_address(self, model):

        if not DEFAULT_ALLOW_DELETE:
            logger.warning(f"DELETE BLOCKED: address {model.name}")
            return

        AddressObject.objects.filter(name=model.name).delete()

    # ============================================================
    # CRUD --> ADDRESS GROUP
    # ============================================================
    @transaction.atomic
    def create_address_group(self, model):
        lg = LogicalGroup.objects.get(name=model.logical_group)
    
        obj = AddressObjectGroup.objects.create(
            name=model.name,
            logical_group=lg,
            description=model.description,
        )
    
        members = AddressObject.objects.filter(
            name__in=model.members,
            logical_group=lg,
        )
        obj.members.set(members)
    
        self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def update_address_group(self, model, diffs):
        obj = AddressObjectGroup.objects.get(
            name=model.name,
            logical_group__name=model.logical_group,
        )
    
        if "members" in diffs:
            members = AddressObject.objects.filter(
                name__in=model.members,
                logical_group__name=model.logical_group,
            )
            obj.members.set(members)
    
        obj.validated_save()
        self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def delete_address_group(self, model):
    
        if not DEFAULT_ALLOW_DELETE:
            logger.warning(f"DELETE BLOCKED: service group {model.name}")
            return
    
        obj = AddressObjectGroup.objects.filter(
            name=model.name,
            logical_group__name=model.logical_group,
        ).first()
    
        if not obj:
            return
    
        if obj.securityrule_set.exists():
            logger.warning(f"DELETE BLOCKED: service group in use")
            return
    
        obj.delete()
    # ============================================================
    # CRUD --> SERVICE
    # ============================================================
    @transaction.atomic
    def create_service(self, model):
    
        lg = LogicalGroup.objects.get(name=model.logical_group)
    
        obj = ServiceObject.objects.create(
            name=model.name,
            logical_group=lg,
            protocol=model.protocol,
            port=model.port,
            description=model.description,
        )
    
        self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def update_service(self, model, diffs):
    
        obj = ServiceObject.objects.get(
            name=model.name,
            logical_group__name=model.logical_group,
        )
    
        changed = False
    
        for field in ["protocol", "port", "description"]:
            if field in diffs:
                setattr(obj, field, getattr(model, field))
                changed = True
    
        if changed:
            obj.validated_save()
    
        if "tags" in diffs:
            self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def delete_service(self, model):
    
        if not DEFAULT_ALLOW_DELETE:
            logger.warning(f"DELETE BLOCKED: service {model.name}")
            return
    
        obj = ServiceObject.objects.filter(
            name=model.name,
            logical_group__name=model.logical_group,
        ).first()
    
        if not obj:
            return
    
        if obj.serviceobjectgroup_set.exists():
            logger.warning(f"DELETE BLOCKED: service {model.name} in use")
            return
    
        obj.delete()

    # ============================================================
    # CRUD --> SERVICE GROUP
    # ============================================================
    @transaction.atomic
    def create_service_group(self, model):
        lg = LogicalGroup.objects.get(name=model.logical_group)
    
        obj = ServiceObjectGroup.objects.create(
            name=model.name,
            logical_group=lg,
            description=model.description,
        )
    
        members = ServiceObject.objects.filter(
            name__in=model.members,
            logical_group=lg,
        )
        obj.members.set(members)
    
        self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def update_service_group(self, model, diffs):
    
        obj = ServiceObjectGroup.objects.get(
            name=model.name,
            logical_group__name=model.logical_group,
        )
    
        if "description" in diffs:
            obj.description = model.description
    
        if "members" in diffs:
            members = ServiceObject.objects.filter(
                name__in=model.members,
                logical_group__name=model.logical_group,
            )
            obj.members.set(members)
    
        obj.validated_save()
    
        if "tags" in diffs:
            self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def delete_service_group(self, model):
    
        if not DEFAULT_ALLOW_DELETE:
            logger.warning(f"DELETE BLOCKED: service group {model.name}")
            return
    
        obj = ServiceObjectGroup.objects.filter(
            name=model.name,
            logical_group__name=model.logical_group,
        ).first()
    
        if not obj:
            return
    
        if obj.securityrule_set.exists():
            logger.warning(f"DELETE BLOCKED: service group in use")
            return
    
        obj.delete()

    # ============================================================
    # CRUD --> APPLICATION
    # ============================================================
    @transaction.atomic
    def create_application(self, model):
        lg = LogicalGroup.objects.get(name=model.logical_group)
    
        obj = ApplicationObject.objects.create(
            name=model.name,
            logical_group=lg,
            description=model.description,
        )
    
        self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def update_application(self, model, diffs):
    
        obj = ApplicationObject.objects.get(
            name=model.name,
            logical_group__name=model.logical_group,
        )
    
        if "description" in diffs:
            obj.description = model.description
            obj.validated_save()
    
        if "tags" in diffs:
            self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def delete_application(self, model):
    
        if not DEFAULT_ALLOW_DELETE:
            logger.warning(f"DELETE BLOCKED: application {model.name}")
            return
    
        obj = ApplicationObject.objects.filter(
            name=model.name,
            logical_group__name=model.logical_group,
        ).first()
    
        if not obj:
            return
    
        if obj.applicationobjectgroup_set.exists():
            logger.warning(f"DELETE BLOCKED: application in use")
            return
    
        obj.delete()

    # ============================================================
    # CRUD --> APPLICATION GROUP
    # ============================================================
    @transaction.atomic
    def create_application_group(self, model):
        lg = LogicalGroup.objects.get(name=model.logical_group)
    
        obj = ApplicationObjectGroup.objects.create(
            name=model.name,
            logical_group=lg,
            description=model.description,
        )
    
        members = ApplicationObject.objects.filter(
            name__in=model.members,
            logical_group=lg,
        )
        obj.members.set(members)
    
        self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def update_application_group(self, model, diffs):
    
        obj = ApplicationObjectGroup.objects.get(
            name=model.name,
            logical_group__name=model.logical_group,
        )
    
        if "description" in diffs:
            obj.description = model.description
    
        if "members" in diffs:
            members = ApplicationObject.objects.filter(
                name__in=model.members,
                logical_group__name=model.logical_group,
            )
            obj.members.set(members)
    
        obj.validated_save()
    
        if "tags" in diffs:
            self.apply_tags(obj, model.tags, prefix="panorama")

    @transaction.atomic
    def delete_application_group(self, model):
    
        if not DEFAULT_ALLOW_DELETE:
            logger.warning(f"DELETE BLOCKED: app group {model.name}")
            return
    
        obj = ApplicationObjectGroup.objects.filter(
            name=model.name,
            logical_group__name=model.logical_group,
        ).first()
    
        if not obj:
            return
    
        if obj.securityrule_set.exists():
            logger.warning(f"DELETE BLOCKED: app group in use")
            return
    
        obj.delete()

    # ============================================================
    # RULE CRUD (ENTERPRISE)
    # ============================================================

    @transaction.atomic
    def create_rule(self, model):

        lg = LogicalGroup.objects.get(name=model.logical_group)

        rule = PolicyRule.objects.create(
            name=model.name,
            logical_group=lg,
            rulebase=model.rulebase,
            index=model.index,
            action=model.action,
            description=model.description,
        )

        self.apply_tags(rule, model.tags, prefix="panorama")

        self._normalize_ordering(lg, model.rulebase)

    @transaction.atomic
    def update_rule(self, model, diffs):

        rule = PolicyRule.objects.get(
            name=model.name,
            logical_group__name=model.logical_group,
        )

        moved = False

        if "index" in diffs:
            self._move_rule(rule, diffs["index"]["new"])
            moved = True

        for field, change in diffs.items():
            if field == "index":
                continue
            setattr(rule, field, change["new"])

        rule.validated_save()
        self.apply_tags(rule, model.tags, prefix="panorama")

        if moved:
            self._normalize_ordering(rule.logical_group, rule.rulebase)

    @transaction.atomic
    def delete_rule(self, model):

        if not DEFAULT_ALLOW_DELETE:
            logger.warning(f"DELETE BLOCKED: rule {model.name}")
            return

        PolicyRule.objects.filter(
            name=model.name,
            logical_group__name=model.logical_group,
        ).delete()

    # ============================================================
    # RULE MOVE ENGINE (restored from hybrid)
    # ============================================================

    def _move_rule(self, rule, new_position):

        old_position = rule.index

        if new_position == old_position:
            return

        if new_position > old_position:
            PolicyRule.objects.filter(
                logical_group=rule.logical_group,
                rulebase=rule.rulebase,
                index__gt=old_position,
                index__lte=new_position,
            ).update(index=F("index") - 1)

        else:
            PolicyRule.objects.filter(
                logical_group=rule.logical_group,
                rulebase=rule.rulebase,
                index__lt=old_position,
                index__gte=new_position,
            ).update(index=F("index") + 1)

        rule.index = new_position
        rule.save(update_fields=["index"])

    def _normalize_ordering(self, logical_group, rulebase):

        rules = PolicyRule.objects.filter(
            logical_group=logical_group,
            rulebase=rulebase,
        ).order_by("index")

        for idx, rule in enumerate(rules, start=1):
            if rule.index != idx:
                rule.index = idx
                rule.save(update_fields=["index"])

    # ============================================================
    # CRUD --> NAT RULE
    # ============================================================
    @transaction.atomic
    def create_nat_rule(self, model):
    
        lg = LogicalGroup.objects.get(name=model.logical_group)
    
        policy, _ = NatPolicy.objects.get_or_create(
            name="default",
            logical_group=lg,
        )
    
        rule = NatPolicyRule.objects.create(
            name=model.name,
            policy=policy,
            index=model.index,
            destination_zone=model.destination_zone,
            source_zone=model.source_zone,
            remark=model.remark,
            log=model.log,
            status=model.status,
        )
    
        self._resolve_nat_m2m(rule, model)
        self._normalize_nat_ordering(policy)

    @transaction.atomic
    def update_nat_rule(self, model, diffs):
    
        rule = NatPolicyRule.objects.get(
            name=model.name,
            policy__logical_group__name=model.logical_group,
        )
    
        moved = False
    
        if "index" in diffs:
            self._move_nat_rule(rule, diffs["index"]["new"])
            moved = True
    
        for field in ["destination_zone", "source_zone", "remark", "log", "status"]:
            if field in diffs:
                setattr(rule, field, getattr(model, field))
    
        rule.validated_save()
    
        if any(k for k in diffs if k.startswith("original_") or k.startswith("translated_")):
            self._resolve_nat_m2m(rule, model)
    
        if moved:
            self._normalize_nat_ordering(rule.policy)

    @transaction.atomic
    def delete_nat_rule(self, model):
    
        if not DEFAULT_ALLOW_DELETE:
            logger.warning(f"DELETE BLOCKED: nat rule {model.name}")
            return
    
        NatPolicyRule.objects.filter(
            name=model.name,
            policy__logical_group__name=model.logical_group,
        ).delete()

    @transaction.atomic
    def _move_nat_rule(self, rule, new_position):
    
        old_position = rule.index
    
        if new_position == old_position:
            return
    
        if new_position > old_position:
            NatPolicyRule.objects.filter(
                policy=rule.policy,
                index__gt=old_position,
                index__lte=new_position,
            ).update(index=F("index") - 1)
        else:
            NatPolicyRule.objects.filter(
                policy=rule.policy,
                index__lt=old_position,
                index__gte=new_position,
            ).update(index=F("index") + 1)
    
        rule.index = new_position
        rule.save(update_fields=["index"])

    @transaction.atomic
    def _normalize_nat_ordering(self, policy):
    
        rules = NatPolicyRule.objects.filter(
            policy=policy
        ).order_by("index")
    
        for idx, rule in enumerate(rules, start=1):
            if rule.index != idx:
                rule.index = idx
                rule.save(update_fields=["index"])

    def _resolve_nat_m2m(self, rule, model):
    
        lg = rule.policy.logical_group
    
        field_map = {
            "original_source_addresses": AddressObject,
            "original_source_address_groups": AddressObjectGroup,
            "original_destination_addresses": AddressObject,
            "original_destination_address_groups": AddressObjectGroup,
            "translated_source_addresses": AddressObject,
            "translated_source_address_groups": AddressObjectGroup,
            "translated_destination_addresses": AddressObject,
            "translated_destination_address_groups": AddressObjectGroup,
            "original_source_services": ServiceObject,
            "original_source_service_groups": ServiceObjectGroup,
            "original_destination_services": ServiceObject,
            "original_destination_service_groups": ServiceObjectGroup,
            "translated_source_services": ServiceObject,
            "translated_source_service_groups": ServiceObjectGroup,
            "translated_destination_services": ServiceObject,
            "translated_destination_service_groups": ServiceObjectGroup,
        }
    
        for field, model_class in field_map.items():
            names = getattr(model, field, [])
            objects = model_class.objects.filter(
                name__in=names,
                logical_group=lg,
            )
            getattr(rule, field).set(objects)

