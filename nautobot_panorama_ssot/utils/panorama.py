from django.db import transaction

def resolve_write_scope(self, object_type: str, model):

    exists = self.object_exists(object_type, model.name, model.logical_group)

    if exists == "shared":
        logger.info(f"{model.name} exists in shared — reusing shared scope")
        return {"location": "shared"}

    return self.resolve_location(model.logical_group)

def resolve_scope(model):
    if model.scope == "shared":
        return "shared"
    return f"device-group/{model.logical_group}"

def create_address(self, model):
    scope_path = resolve_scope(model)
    self.client.create_address(model, scope=scope_path)

def normalize_rule_positions(logical_group, rulebase):
    """
    Normalize rule positions for a specific logical group + rulebase.

    Ensures:
    - Positions start at 1
    - Sequential with no gaps
    - No duplicates
    - Deterministic ordering
    """

    from nautobot_firewall_models.models import PolicyRule

    with transaction.atomic():

        rules = (
            PolicyRule.objects
            .filter(logical_group=logical_group, rulebase=rulebase)
            .order_by("index", "pk")
        )

        for new_position, rule in enumerate(rules, start=1):
            if rule.index != new_position:
                rule.index = new_position
                rule.save(update_fields=["index"])

def _normalize_rule(self, entry: dict) -> dict:

    return {
        "name": entry.get("@name"),
        "action": entry.get("action"),
        "description": entry.get("description", ""),

        "source": self._extract_members(entry.get("source")),
        "source_groups": [],  # optional split if you support groups separately

        "destination": self._extract_members(entry.get("destination")),
        "destination_groups": [],

        "service": self._extract_members(entry.get("service")),
        "service_groups": [],

        "application": self._extract_members(entry.get("application")),
        "application_groups": [],
    }
