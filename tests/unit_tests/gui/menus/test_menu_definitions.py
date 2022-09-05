import builtins
import pytest
from ode_solver.gui.menus import menu_configuration, get_menu_definition, get_menu_callbacks


@pytest.fixture()
def menu_definition():
    return {
        "Menu": {
            "Sub-Menu": {
                "Option 1": builtins.print
            },
            "Option 2": builtins.print
        }
    }


def test_get_menu_definitions(menu_definition, monkeypatch):
    monkeypatch.setattr(menu_configuration, "MENU", menu_definition)
    definition = get_menu_definition()
    assert [["Menu", ["Sub-Menu", ["Option 1"], "Option 2"]]] == definition


def test_get_menu_callbacks(menu_definition, monkeypatch):
    monkeypatch.setattr(menu_configuration, "MENU", menu_definition)
    callbacks = get_menu_callbacks()
    assert 2 == len(callbacks)
    assert builtins.print == callbacks["Option 1"]
    assert builtins.print == callbacks["Option 2"]
