"""Utilities for DiffSync related stuff."""

from typing import Optional
from collections import defaultdict

from django.contrib.contenttypes.models import ContentType
from django.utils.text import slugify
from nautobot.extras.models import CustomField, Tag
from nautobot_panorama_ssot.diffsync.models.base import (
    ControlPlaneModel,
    VirtualSystemModel,
    LogicalGroupModel,
    TagModel,
    AddressModel,
    AddressGroupModel,
    ServiceModel,
    ServiceGroupModel,
    RuleModel,
)

from nautobot_panorama_ssot.constant import TAG_COLOR

# rule optimization & duplicate object detection
def detect_rule_shadowing(rules):

    shadowed = []

    for i, rule_a in enumerate(rules):
        for rule_b in rules[i+1:]:

            if (
                set(rule_a["source"]) >= set(rule_b["source"]) and
                set(rule_a["destination"]) >= set(rule_b["destination"]) and
                rule_a["action"] == rule_b["action"]
            ):
                shadowed.append((rule_a["name"], rule_b["name"]))

    return shadowed

def detect_duplicate_objects(objects_by_dg):
    """
    objects_by_dg = {
        "DG1": [{"name": ..., "value": ...}],
        "DG2": [...]
    }
    """

    seen = {}
    duplicates = []

    for dg, objects in objects_by_dg.items():
        for obj in objects:
            key = (obj["name"], obj.get("value"))
            if key in seen and seen[key] != dg:
                duplicates.append((obj["name"], seen[key], dg))
            else:
                seen[key] = dg

    return duplicates

def suggest_rule_consolidation(rules):
    """
    Suggest consolidation candidates.
    Returns list of (rule_a, rule_b)
    """

    suggestions = []

    for i, rule_a in enumerate(rules):
        for rule_b in rules[i + 1:]:

            if (
                rule_a.get("action") == rule_b.get("action")
                and rule_a.get("from") == rule_b.get("from")
                and rule_a.get("to") == rule_b.get("to")
                and set(rule_a.get("service", [])) == set(rule_b.get("service", []))
            ):
                suggestions.append((rule_a.get("@name"), rule_b.get("@name")))

    return suggestions

def suggest_rule_reordering(rules, hit_counts):
    """
    Suggest rule reordering based on hit count.
    Returns list of (rule_name, suggested_position)
    """

    # Map hit counts
    hits = {r["rule-name"]: r.get("hit-count", 0) for r in hit_counts}

    # Sort rules by descending hit count
    ordered = sorted(rules, key=lambda r: hits.get(r["@name"], 0), reverse=True)

    suggestions = []

    for index, rule in enumerate(ordered):
        if rules[index]["@name"] != rule["@name"]:
            suggestions.append((rule["@name"], index))

    return suggestions

def analyze_hit_counts(hit_counts, threshold=0):

    unused = []

    for rule in hit_counts:
        if rule.get("hit-count", 0) <= threshold:
            unused.append(rule.get("rule-name"))

    return unused

def calculate_rule_risk(rule):

    score = 0

    if "any" in rule.get("source", []):
        score += 3

    if "any" in rule.get("destination", []):
        score += 3

    if "any" in rule.get("service", []):
        score += 2

    if rule.get("action") == "allow":
        score += 2

    if "untrust" in rule.get("from", []):
        score += 3

    return score

def generate_cleanup_suggestions(
    unused_rules,
    shadowed_rules,
    duplicate_objects,
):

    suggestions = []

    for rule in unused_rules:
        suggestions.append(f"Rule '{rule}' has zero hits — consider removal")

    for upper, lower in shadowed_rules:
        suggestions.append(f"Rule '{lower}' is shadowed by '{upper}'")

    for name, dg1, dg2 in duplicate_objects:
        suggestions.append(f"Duplicate object '{name}' in {dg1} and {dg2}")

    return suggestions

# used in adapters to determine pre/post
def resolve_scope(model):
    if model.scope == "shared":
        return self.shared
    return self.device_groups[model.logical_group]

def create_tag_sync_from_panorama():
    """Create tag for tagging objects that have been created by Panorama."""
    tag, _ = Tag.objects.get_or_create(
        name="SSoT Synced from panorama",
        defaults={
            "name": "SSoT Synced from panorama",
            "description": "Object synced at some point from panorama",
            "color": TAG_COLOR,
        },
    )
    for model in [NautobotAddress, NautobotAddressGroup, NautobotService, NautobotServiceGroup, NautobotApplication, NautobotApplicationGroup ]:
        tag.content_types.add(ContentType.objects.get_for_model(model))
    return tag

def get_valid_custom_fields(cfs: dict, excluded_cfs: Optional[list] = None):
    """Remove custom fields that are on the excluded list.

    Args:
        cfs: custom fields
        excluded_cfs: list of excluded custom fields
    """
    if excluded_cfs is None:
        excluded_cfs = []
    default_excluded_cfs = [
        "dhcp_ranges",
        "dns_a_record_comment",
        "dns_host_record_comment",
        "dns_ptr_record_comment",
        "fixed_address_comment",
        "mac_address",
        "ssot_synced_to_panorama",
    ]
    excluded_cfs.extend(default_excluded_cfs)
    valid_cfs = {}
    for cf_name, val in cfs.items():
        if cf_name in excluded_cfs:
            continue
        valid_cfs[cf_name] = val

    return valid_cfs


def get_default_custom_fields(cf_contenttype: ContentType, excluded_cfs: Optional[list] = None) -> dict:
    """Get default Custom Fields for specific ContentType.

    Args:
        cf_contenttype (ContentType): Specific ContentType to get all Custom Fields for.

    Returns:
        dict: Dictionary of all Custom Fields for a specific object type.
    """
    if excluded_cfs is None:
        excluded_cfs = []
    customfields = CustomField.objects.filter(content_types=cf_contenttype)
    # These cfs are always excluded
    default_excluded_cfs = [
        "dhcp_ranges",
        "dns_a_record_comment",
        "dns_host_record_comment",
        "dns_ptr_record_comment",
        "fixed_address_comment",
        "mac_address",
        "ssot_synced_to_infoblox",
    ]
    # User defined excluded cfs
    excluded_cfs.extend(default_excluded_cfs)
    default_cfs = {}
    for customfield in customfields:
        if customfield.key in excluded_cfs:
            continue
        if customfield.key not in default_cfs:
            default_cfs[customfield.key] = None
    return default_cfs


class DriftAudit:

    def __init__(self):
        self.operations = []
        self.rule_impacts = {}

    def record(self, action, object_type, name, scope):
        self.operations.append({
            "action": action,
            "type": object_type,
            "name": name,
            "scope": scope,
        })

    def record_rule_impact(self, rule_name, object_name):
        self.rule_impacts.setdefault(rule_name, []).append(object_name)

    def summary(self):
        from collections import Counter
        return Counter(op["action"] for op in self.operations)

    def export(self):
        return self.operations

class DependencyGraph:

    def __init__(self):
        self.graph = defaultdict(set)

    def add_dependency(self, parent, child):
        self.graph[parent].add(child)

    def topological_sort(self):
        visited = set()
        order = []

        def visit(node):
            if node in visited:
                return
            visited.add(node)
            for child in self.graph[node]:
                visit(child)
            order.append(node)

        for node in list(self.graph.keys()):
            visit(node)

        return order[::-1]

