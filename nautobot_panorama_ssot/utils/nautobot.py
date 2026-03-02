"""Nautobot Helpers"""

def get_logical_group(self, name: str):
    return LogicalGroup.objects.get(name=name)
