import pytest
from src.ode_solver.options.option_reasons import OptionReason
from src.ode_solver.options import option_definitions


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
    options = option_definitions.get_current_options()
    assert 2 == len(options)
    assert "limit" in options.keys()
    assert "steps" in options.keys()


def test_get_values_from_options(simulation_options, monkeypatch):
    monkeypatch.setattr(option_definitions, "SIMULATION_OPTIONS", simulation_options)
    values = option_definitions.get_values_from_current_options()
    assert 2 == len(values)
    assert "20.0" == values["limit"]
    assert "10" == values["steps"]


def test_set_options_from_values(simulation_options, simulation_values, monkeypatch):
    monkeypatch.setattr(option_definitions, "SIMULATION_OPTIONS", simulation_options)
    option_definitions.set_current_options_from_values(simulation_values)
    values = option_definitions.get_values_from_current_options()
    assert 2 == len(values)
    assert "123.0" == values["limit"]
    assert "52" == values["steps"]


def test_set_options_from_values_ignores_unrecognised_value(simulation_options, simulation_values, monkeypatch):
    monkeypatch.setattr(option_definitions, "SIMULATION_OPTIONS", simulation_options)
    simulation_values["unrecognised"] = "Some Value"
    option_definitions.set_current_options_from_values(simulation_values)
    values = option_definitions.get_values_from_current_options()
    assert 2 == len(values)
    assert "123.0" == values["limit"]
    assert "52" == values["steps"]
