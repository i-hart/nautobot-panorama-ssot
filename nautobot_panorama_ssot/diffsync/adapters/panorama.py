"""
Production Panorama DiffSync Adapter
Enterprise-ready implementation (Corrected + Deterministic)
"""

import datetime
import time
from diffsync import DiffSync
from concurrent.futures import ThreadPoolExecutor

from nautobot_panorama_ssot.diffsync.models.base import *
from nautobot_panorama_ssot.utils.client import PanoramaClient
from nautobot_panorama_ssot.utils.forward import ForwardClient
from nautobot_panorama_ssot.constant import (
    DEFAULT_SAFE_COMMIT_THRESHOLD,
    DEFAULT_ALLOWED_HOURS,
)

from nautobot_panorama_ssot.utils.compliance import COMPLIANCE_QUERY_MAP
from nautobot_panorama_ssot.utils.diffsync import (
    DriftAudit,
    calculate_rule_risk,
)


class PanoramaAdapter(DiffSync):

    model_priority = {
        "tag": 100,
        "address": 90,
        "address_group": 80,
        "service": 70,
        "service_group": 60,
        "application": 50,
        "application_group": 40,
        "nat_rule": 20,
        "rule": 10,
    }

    control_plane = ControlPlaneModel
    logical_group = LogicalGroupModel

    tag = TagModel
    address = AddressModel
    address_group = AddressGroupModel
    service = ServiceModel
    service_group = ServiceGroupModel
    application = ApplicationModel
    application_group = ApplicationGroupModel
    rule = RuleModel
    nat_rule = NatRuleModel

    top_level = ["control_plane"]

    # ===========================================================
    # INIT
    # ===========================================================
    def __init__(
        self,
        control_plane,
        base_url,
        api_key,
        verify_ssl,
        timeout,
        logger,
        forward_creds=None,
        simulation_mode=False,
        drift_only=False,
        change_window_only=False,
        safe_commit_mode="advisory",
        require_approval=False,
        enable_compliance_checks=True,
        enable_blast_radius=True,
        enable_risk_scoring=True,
        enable_rule_optimizer=True,
    ):
        super().__init__()

        self.control_plane_obj = control_plane
        self.logger = logger

        self.client = PanoramaClient(
            base_url=base_url,
            api_key=api_key,
            verify_ssl=verify_ssl,
            timeout=timeout,
        )

        self.forward = None
        if forward_creds:
            self.forward = ForwardClient(
                base_url=forward_creds["base_url"],
                token=forward_creds["token"],
            )

        self.touched_device_groups = set()
        self.audit = DriftAudit()

        # Runtime flags ONLY (no constants)
        self.simulation_mode = simulation_mode
        self.drift_only = drift_only
        self.change_window_only = change_window_only
        self.safe_commit_mode = safe_commit_mode.lower()
        self.require_approval = require_approval
        self.enable_compliance_checks = enable_compliance_checks
        self.enable_blast_radius = enable_blast_radius
        self.enable_risk_scoring = enable_risk_scoring
        self.enable_rule_optimizer = enable_rule_optimizer

    # ===========================================================
    # LOAD
    # ===========================================================

    def load(self):

        cp = self.control_plane(
            name=self.client.name,
            description="Panorama Control Plane",
        )
        self.add(cp)

        device_groups = self.client.get_device_groups()
        scopes = ["shared"] + [dg["name"] for dg in device_groups]

        for dg in scopes:

            lg = self.logical_group(
                name=dg,
                virtual_system="shared",
            )
            self.add(lg)
            cp.add_child(lg)

            self._load_tags(lg)
            self._load_addresses(lg)
            self._load_address_groups(lg)
            self._load_services(lg)
            self._load_service_groups(lg)
            self._load_applications(lg)
            self._load_application_groups(lg)
            self._load_security_rules(lg)
            self._load_nat_rules(lg)

    # -----------------------------------------------------------
    # Load Helpers
    # -----------------------------------------------------------

    def _extract_members(self, block):

        if not block:
            return []

        if isinstance(block, str):
            return [block]

        if isinstance(block, list):
            return block

        if isinstance(block, dict):
            members = block.get("member", [])
            if isinstance(members, str):
                return [members]
            if isinstance(members, list):
                return members

        return []

    # ---------------- TAG ----------------

    def _load_tags(self, lg):

        for obj in self.client.get_tags(lg.name):
            self.add(
                self.tag(
                    name=obj["name"],
                    logical_group=lg.name,
                    color=obj.get("color"),
                )
            )

    # ---------------- ADDRESS ----------------

    def _load_addresses(self, lg):

        for obj in self.client.get_address_objects(lg.name):
            self.add(
                self.address(
                    name=obj["name"],
                    logical_group=lg.name,
                    value=obj["value"],
                    address_type=obj.get("type", "ip-netmask"),
                    description=obj.get("description", ""),
                    tags=obj.get("tag", []),
                )
            )

    def _load_address_groups(self, lg):

        for obj in self.client.get_address_groups(lg.name):
            self.add(
                self.address_group(
                    name=obj["name"],
                    logical_group=lg.name,
                    description=obj.get("description", ""),
                    members=obj.get("static", []),
                    tags=obj.get("tag", []),
                )
            )

    # ---------------- SERVICE ----------------

    def _load_services(self, lg):

        for obj in self.client.get_service_objects(lg.name):
            self.add(
                self.service(
                    name=obj["name"],
                    logical_group=lg.name,
                    protocol=obj["protocol"],
                    port=obj["port"],
                    description=obj.get("description", ""),
                    tags=obj.get("tag", []),
                )
            )

    def _load_service_groups(self, lg):

        for obj in self.client.get_service_groups(lg.name):
            self.add(
                self.service_group(
                    name=obj["name"],
                    logical_group=lg.name,
                    description=obj.get("description", ""),
                    members=obj.get("members", []),
                    tags=obj.get("tag", []),
                )
            )

    # ---------------- APPLICATION ----------------

    def _load_applications(self, lg):

        for obj in self.client.get_application_objects(lg.name):
            self.add(
                self.application(
                    name=obj["name"],
                    logical_group=lg.name,
                    description=obj.get("description", ""),
                    category=obj.get("category"),
                    subcategory=obj.get("subcategory"),
                    technology=obj.get("technology"),
                    risk=int(obj.get("risk", 0) or 0),
                    tags=obj.get("tag", []),
                )
            )

    def _load_application_groups(self, lg):

        for obj in self.client.get_application_groups(lg.name):
            self.add(
                self.application_group(
                    name=obj["name"],
                    logical_group=lg.name,
                    description=obj.get("description", ""),
                    members=obj.get("members", []),
                    tags=obj.get("tag", []),
                )
            )

    # ---------------- SECURITY RULE ----------------

    def _load_security_rules(self, lg):

        for rulebase in ["pre", "post"]:

            rules = self.client.get_security_rules(
                device_group=lg.name,
                rulebase=rulebase,
            )

            for position, entry in enumerate(rules):

                self.add(
                    self.rule(
                        name=entry.get("@name") or entry.get("name"),
                        logical_group=lg.name,
                        rulebase=rulebase,
                        position=position,
                        action=entry.get("action"),
                        description=entry.get("description", ""),
                        source=self._extract_members(entry.get("source")),
                        destination=self._extract_members(entry.get("destination")),
                        service=self._extract_members(entry.get("service")),
                        application=self._extract_members(entry.get("application")),
                        tags=self._extract_members(entry.get("tag")),
                    )
                )

    # ---------------- NAT RULE ----------------

    def _load_nat_rules(self, lg):

        for rulebase in ["pre", "post"]:

            rules = self.client.get_nat_rules(
                device_group=lg.name,
                rulebase=rulebase,
            )

            for position, entry in enumerate(rules):

                self.add(
                    self.nat_rule(
                        name=entry.get("@name") or entry.get("name"),
                        logical_group=lg.name,
                        rulebase=rulebase,
                        position=position,
                        **entry
                    )
                )

    # ===========================================================
    # DELETE GUARD
    # ===========================================================
    def _delete_guard(self, model, object_type):

        if self.drift_only:
            return False

        if self.client.is_object_in_use(model):
            raise Exception(f"{object_type} {model.name} is referenced")

        if object_type == "rule" and self.forward and self.enable_blast_radius:
            impact = self.forward.blast_radius(model.name)
            if impact:
                raise RuntimeError(
                    f"Delete blocked: rule {model.name} affects {len(impact)} flows"
                )

        return True

    # ===========================================================
    # CRUD CORE
    # ===========================================================
    def _mark_touched(self, model):
        if hasattr(model, "logical_group"):
            self.touched_device_groups.add(model.logical_group)

    def _create(self, method, model, object_type):

        if self.drift_only:
            self.audit.record("create", object_type, model.name, model.logical_group)
            return

        if self.simulation_mode:
            self.logger.info(f"[SIMULATION] Would create {object_type} {model.name}")
            return

        scope = self.client.resolve_write_scope(object_type, model)
        method(model, scope=scope)
        self._mark_touched(model)

    def _update(self, method, model, diffs, object_type):

        if self.drift_only:
            self.audit.record("update", object_type, model.name, model.logical_group)
            return

        if self.simulation_mode:
            self.logger.info(f"[SIMULATION] Would update {object_type} {model.name}")
            return

        method(model, diffs)
        self._mark_touched(model)

    def _delete(self, method, model, object_type):

        if self.drift_only:
            self.audit.record("delete", object_type, model.name, model.logical_group)
            return

        if self.simulation_mode:
            self.logger.info(f"[SIMULATION] Would delete {object_type} {model.name}")
            return

        if self.enable_blast_radius:
            self._run_blast_radius_check(model)

        if not self._delete_guard(model, object_type):
            return

        method(model)
        self._mark_touched(model)

    # ===========================================================
    # CRUD WRAPPERS (COMPLETE)
    # ===========================================================
    def create_tag(self, m): self._create(self.client.create_tag, m, "tag")
    def update_tag(self, m, d): self._update(self.client.update_tag, m, d, "tag")
    def delete_tag(self, m): self._delete(self.client.delete_tag, m, "tag")

    def create_address(self, m): self._create(self.client.create_address, m, "address")
    def update_address(self, m, d): self._update(self.client.update_address, m, d, "address")
    def delete_address(self, m): self._delete(self.client.delete_address, m, "address")

    def create_address_group(self, m): self._create(self.client.create_address_group, m, "address_group")
    def update_address_group(self, m, d): self._update(self.client.update_address_group, m, d, "address_group")
    def delete_address_group(self, m): self._delete(self.client.delete_address_group, m, "address_group")

    def create_service(self, m): self._create(self.client.create_service, m, "service")
    def update_service(self, m, d): self._update(self.client.update_service, m, d, "service")
    def delete_service(self, m): self._delete(self.client.delete_service, m, "service")

    def create_service_group(self, m): self._create(self.client.create_service_group, m, "service_group")
    def update_service_group(self, m, d): self._update(self.client.update_service_group, m, d, "service_group")
    def delete_service_group(self, m): self._delete(self.client.delete_service_group, m, "service_group")

    def create_application(self, m): self._create(self.client.create_application, m, "application")
    def update_application(self, m, d): self._update(self.client.update_application, m, d, "application")
    def delete_application(self, m): self._delete(self.client.delete_application, m, "application")

    def create_application_group(self, m): self._create(self.client.create_application_group, m, "application_group")
    def update_application_group(self, m, d): self._update(self.client.update_application_group, m, d, "application_group")
    def delete_application_group(self, m): self._delete(self.client.delete_application_group, m, "application_group")

    def create_rule(self, m): self._create(self.client.create_rule, m, "rule")
    def update_rule(self, m, d): self._update(self.client.update_rule, m, d, "rule")
    def delete_rule(self, m): self._delete(self.client.delete_rule, m, "rule")

    def create_nat_rule(self, m): self._create(self.client.create_nat_rule, m, "nat_rule")
    def update_nat_rule(self, m, d): self._update(self.client.update_nat_rule, m, d, "nat_rule")
    def delete_nat_rule(self, m): self._delete(self.client.delete_nat_rule, m, "nat_rule")

    # ===========================================================
    # FINALIZE (SAFE + FIXED)
    # ===========================================================
    def finalize(self):

        if self.drift_only or self.simulation_mode:
            self.logger.info("Skipping commit phase (drift/simulation)")
            return

        if self.change_window_only:
            hour = datetime.datetime.utcnow().hour
            if not (DEFAULT_ALLOWED_HOURS[0] <= hour <= DEFAULT_ALLOWED_HOURS[1]):
                raise Exception("Outside approved change window")

        self.client.execute_batch()

        compliance_failures = []
        if self.enable_compliance_checks and self.forward:
            for framework, queries in COMPLIANCE_QUERY_MAP.items():
                for q in queries:
                    if self.forward.run_nqe(q):
                        compliance_failures.append(q)

        risk_scores = []
        if self.enable_risk_scoring:
            for dg in self.touched_device_groups:
                rules = self.client.get_security_rules(dg, "pre")
                for rule in rules:
                    risk_scores.append(calculate_rule_risk(rule))

        safe_score = 100
        if compliance_failures:
            safe_score -= 30
        safe_score -= sum(1 for r in risk_scores if r >= 8) * 5

        if (
            self.safe_commit_mode == "enforced"
            and safe_score < DEFAULT_SAFE_COMMIT_THRESHOLD
        ):
            raise Exception("Safe-to-Commit threshold failed")

        for dg in self.touched_device_groups:
            job_id = self.client.commit_device_group(dg)
            status = self.client.monitor_commit(job_id)

            if status != "FIN":
                self.client.rollback_device_group(dg)
                raise Exception(f"Commit failed in {dg}")
