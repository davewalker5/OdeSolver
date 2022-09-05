import pytest
from ode_solver.gui.options import OptionReason
from ode_solver.gui.options import option_definitions
from ode_solver.gui.options.option_definitions import get_current_options, get_values_from_current_options, \
    set_current_options_from_values


@pytest.fixture()
def simulation_options():
    return {
        "limit": {
            "value": "20.0",
            "prompt": "Limit of x",
            "type": "decimal",
            "items": None,
            "events": True,
            "group": "Simulation Parameters",
            "required": True,
            "valid": True,
            "reason": OptionReason.OK
        },
        "steps": {
            "value": "10",
            "prompt": "No. steps",
            "type": "decimal",
            "items": None,
            "events": True,
            "group": "Simulation Parameters",
            "required": True,
            "valid": True,
            "reason": OptionReason.OK
        }
    }


@pytest.fixture()
def simulation_values():
    return {
        "limit": "123.0",
        "steps": "52"
    }


def test_get_current_options(simulation_options, monkeypatch):
    monkeypatch.setattr(option_definitions, "SIMULATION_OPTIONS", simulation_options)
    options = get_current_options()
    assert 2 == len(options)
    assert "limit" in options.keys()
    assert "steps" in options.keys()


def test_get_values_from_options(simulation_options, monkeypatch):
    monkeypatch.setattr(option_definitions, "SIMULATION_OPTIONS", simulation_options)
    values = get_values_from_current_options()
    assert 2 == len(values)
    assert "20.0" == values["limit"]
    assert "10" == values["steps"]


def test_set_options_from_values(simulation_options, simulation_values, monkeypatch):
    monkeypatch.setattr(option_definitions, "SIMULATION_OPTIONS", simulation_options)
    set_current_options_from_values(simulation_values)
    values = get_values_from_current_options()
    assert 2 == len(values)
    assert "123.0" == values["limit"]
    assert "52" == values["steps"]


def test_set_options_from_values_ignores_unrecognised_value(simulation_options, simulation_values, monkeypatch):
    monkeypatch.setattr(option_definitions, "SIMULATION_OPTIONS", simulation_options)
    simulation_values["unrecognised"] = "Some Value"
    set_current_options_from_values(simulation_values)
    values = get_values_from_current_options()
    assert 2 == len(values)
    assert "123.0" == values["limit"]
    assert "52" == values["steps"]
