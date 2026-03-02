class ForwardQueryLibrary:

    def __init__(self, forward_client):
        self.forward = forward_client

    # ----------------------------------
    # Compliance Queries
    # ----------------------------------

    def pci_exposure(self):
        return 'flows | where dst_zone == "pci" and src_zone == "untrust"'

    def unknown_apps(self):
        return 'flows | where app == "unknown-tcp"'

    def any_any_rules(self):
        return 'flows | where src_zone == "any" and dst_zone == "any"'

    # ----------------------------------
    # Risk Queries
    # ----------------------------------

    def high_volume_rule(self, rule_name):
        return f'flows | where rule == "{rule_name}" | stats count()'

    # ----------------------------------
    # Execute
    # ----------------------------------

    def validate(self, queries):
        return self.forward.validate_queries(queries)

