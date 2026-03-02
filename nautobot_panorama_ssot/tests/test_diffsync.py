"""Tests for diffsync"""

import pytest
from nautobot_panorama_ssot.diffsync.adapters.panorama import PanoramaAdapter

def test_rule_diff():

    source = PanoramaAdapter(MockPanorama(), logger=None)
    target = NautobotAdapter(job=None, sync=None)

    source.load()
    target.load()

    diff = source.diff_to(target)

    assert diff is not None

class MockPanorama:
    def get_device_groups(self):
        return [{"name": "DG1"}]

class MockClient:

    def __init__(self):
        self.objects = {}

    def get_device_groups(self):
        return [{"name": "DG1"}]

    def get_tags(self, dg):
        return []

    def get_address_objects(self, dg):
        return []

    def get_security_rules(self, dg, rb):
        return []

    def commit_device_group(self, dg):
        pass


@pytest.fixture
def adapter():
    mock = MockClient()
    return PanoramaAdapter(mock, logger=None)


def test_load(adapter):
    adapter.load()
    assert adapter.get_all("control_plane")


def test_drift_mode(monkeypatch, adapter):
    from nautobot_panorama_ssot.constant import DEFAULT_DRIFT_ONLY
    monkeypatch.setattr("nautobot_panorama_ssot.constant.DEFAULT_DRIFT_ONLY", True)

    # simulate create
    model = adapter.address(
        name="Test1",
        logical_group="shared",
        value="1.1.1.1",
        address_type="ip-netmask",
    )

    adapter.create_address(model)

    assert adapter.audit.operations
