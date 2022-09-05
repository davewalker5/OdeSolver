import pytest
from ode_solver.gui.options.option_validator import capture_all_values


@pytest.fixture()
def simulation_options():
    return {
        "option_1": {"value": ""},
        "option_2": {"value": ""},
        "option_3": {"value": ""}
    }


@pytest.fixture()
def option_values():
    return {
        "option_1": 1,
        "option_2": 2,
        "option_3": 3
    }


def test_can_create_value_list(simulation_options, option_values):
    capture_all_values(simulation_options, option_values)
    assert 1 == simulation_options["option_1"]["value"]
    assert 2 == simulation_options["option_2"]["value"]
    assert 3 == simulation_options["option_3"]["value"]


def test_value_list_creation_ignores_unrecognised_keys(simulation_options, option_values):
    option_values["option_4"] = 4
    capture_all_values(simulation_options, option_values)
    assert "option_4" not in simulation_options.keys()
    assert 1 == simulation_options["option_1"]["value"]
    assert 2 == simulation_options["option_2"]["value"]
    assert 3 == simulation_options["option_3"]["value"]
