from ode_solver.gui.options.integration_methods import IntegrationMethods
from ode_solver.gui.options.option_reasons import OptionReason

SIMULATION_OPTIONS = {
    "function_file": {
        "value": "",
        "prompt": "Function file",
        "type": "file",
        "items": None,
        "events": False,
        "group": "Simulation Parameters",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "method": {
        "value": "",
        "prompt": "Method",
        "type": "list",
        "items": IntegrationMethods.method_name_list(),
        "events": False,
        "group": "Simulation Parameters",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "limit": {
        "value": "",
        "prompt": "Limit of x",
        "type": "decimal",
        "items": None,
        "events": True,
        "group": "Simulation Parameters",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "steps": {
        "value": "",
        "prompt": "No. steps",
        "type": "decimal",
        "items": None,
        "events": True,
        "group": "Simulation Parameters",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "step_size": {
        "value": "",
        "prompt": "Initial step size",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Simulation Parameters",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "initial_value": {
        "value": "",
        "prompt": "Initial y",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Simulation Parameters",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "tolerance": {
        "value": "",
        "prompt": "Tolerance",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Step Adjustment",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "adjust_step_size": {
        "value": False,
        "prompt": "Adjust step size",
        "type": "checkbox",
        "items": None,
        "events": False,
        "group": "Step Adjustment",
        "required": True,
        "valid": True,
        "reason": OptionReason.OK
    },
    "chart_title": {
        "value": "",
        "prompt": "Title",
        "type": "text",
        "items": None,
        "events": False,
        "group": "Chart Properties",
        "required": False,
        "valid": True,
        "reason": OptionReason.OK
    },
    "chart_min_y": {
        "value": "",
        "prompt": "Y(min)",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Chart Properties",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "chart_max_y": {
        "value": "",
        "prompt": "Y(max)",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Chart Properties",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "chart_max_x": {
        "value": "",
        "prompt": "X(max)",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Chart Properties",
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "chart_auto_scale": {
        "value": True,
        "prompt": "Automatic scaling",
        "type": "checkbox",
        "items": None,
        "events": False,
        "group": "Chart Properties",
        "required": True,
        "valid": True,
        "reason": OptionReason.OK
    }
}


def get_current_options():
    """
    Return the current simulation options, including menu configuration data

    :return: Dictionary of options
    """
    return SIMULATION_OPTIONS


def get_values_from_current_options():
    """
    Return a dictionary of option key-value-pairs for the current simulation options,
    removing the menu configuration information from the dictionary of options
    """
    simulation_options = {k: v["value"] for k, v in SIMULATION_OPTIONS.items()}
    return simulation_options


def set_current_options_from_values(simulation_options):
    """
    Set the values in the simulation configuration from the specified options dictionary

    :param simulation_options: Dictionary of option key-value pairs
    """
    for key, value in simulation_options.items():
        if key in SIMULATION_OPTIONS.keys():
            SIMULATION_OPTIONS[key]["value"] = value
