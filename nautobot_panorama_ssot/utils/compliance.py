PCI_REQUIREMENTS = {
    "no_any_any_allow": "PCI-DSS 1.2.1",
    "restrict_inbound_untrust": "PCI-DSS 1.3.1",
}

NIST_REQUIREMENTS = {
    "least_privilege": "NIST AC-6",
    "deny_by_default": "NIST SC-7",
}

CIS_REQUIREMENTS = {
    "restrict_any_service": "CIS 3.2",
}

def evaluate_compliance(rule):
    
    findings = []
    
    if (
        "any" in rule.get("source", [])
        and "any" in rule.get("destination", [])
        and rule.get("action") == "allow"
    ):
        findings.append("no_any_any_allow")
    
    if "untrust" in rule.get("from", []) and rule.get("action") == "allow":
        findings.append("restrict_inbound_untrust")
    
    return findings


COMPLIANCE_QUERY_MAP = {

    "PCI": [
        'flows | where dst_zone == "cardholder" and src_zone == "untrust"',
    ],

    "NIST": [
        'flows | where app == "unknown-tcp"',
    ],

    "CIS": [
        'flows | where service == "any"',
    ],
}
