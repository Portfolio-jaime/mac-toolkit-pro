import pytest
from mac_toolkit_pro.monitors.base import BaseMonitor


class ConcreteMonitor(BaseMonitor):
    name = "test"

    def snapshot(self):
        return {"value": 42}

    def display(self):
        pass


def test_base_monitor_has_name():
    m = ConcreteMonitor()
    assert m.name == "test"


def test_base_monitor_snapshot_returns_dict():
    m = ConcreteMonitor()
    result = m.snapshot()
    assert isinstance(result, dict)
    assert result["value"] == 42


def test_base_monitor_cannot_instantiate_directly():
    with pytest.raises(TypeError):
        BaseMonitor()
