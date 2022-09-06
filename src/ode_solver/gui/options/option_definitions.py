from ode_solver.gui.options.integration_methods import IntegrationMethods
from ode_solver.gui.options.option_reasons import OptionReason

GROUP_NAME_FUNCTION_DEFINITION = "Function"
GROUP_NAME_SIMULATION_PARAMETERS = "Simulation Parameters"
GROUP_NAME_STEP_ADJUSTMENT = "Step Adjustment"
GROUP_NAME_CHART_PROPERTIES = "Chart Properties"


SIMULATION_OPTIONS = {
    "function": {
        "value": "",
        "prompt": "Function Definition",
        "type": "textarea",
        "width": 80,
        "height": 24,
        "items": None,
        "events": False,
        "group": GROUP_NAME_FUNCTION_DEFINITION,
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "method": {
        "value": "",
        "prompt": "Method",
        "type": "list",
        "width": 0,
        "height": 0,
        "items": IntegrationMethods.method_name_list(),
        "events": False,
        "group": GROUP_NAME_SIMULATION_PARAMETERS,
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "limit": {
        "value": "",
        "prompt": "Limit of x",
        "type": "decimal",
        "width": 0,
        "height": 0,
        "items": None,
        "events": True,
        "group": GROUP_NAME_SIMULATION_PARAMETERS,
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "steps": {
        "value": "",
        "prompt": "No. steps",
        "type": "decimal",
        "width": 0,
        "height": 0,
        "items": None,
        "events": True,
        "group": GROUP_NAME_SIMULATION_PARAMETERS,
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "step_size": {
        "value": "",
        "prompt": "Initial step size",
        "type": "decimal",
        "width": 0,
        "height": 0,
        "items": None,
        "events": False,
        "group": GROUP_NAME_SIMULATION_PARAMETERS,
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "initial_value": {
        "value": "",
        "prompt": "Initial y",
        "type": "decimal",
        "width": 0,
        "height": 0,
        "items": None,
        "events": False,
        "group": GROUP_NAME_SIMULATION_PARAMETERS,
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "tolerance": {
        "value": "",
        "prompt": "Tolerance",
        "type": "decimal",
        "width": 0,
        "height": 0,
        "items": None,
        "events": False,
        "group": GROUP_NAME_STEP_ADJUSTMENT,
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "adjust_step_size": {
        "value": False,
        "prompt": "Adjust step size",
        "type": "checkbox",
        "width": 0,
        "height": 0,
        "items": None,
        "events": False,
        "group": GROUP_NAME_STEP_ADJUSTMENT,
        "required": True,
        "valid": True,
        "reason": OptionReason.OK
    },
    "chart_title": {
        "value": "",
        "prompt": "Title",
        "type": "text",
        "width": 0,
        "height": 0,
        "items": None,
        "events": False,
        "group": GROUP_NAME_CHART_PROPERTIES,
        "required": False,
        "valid": True,
        "reason": OptionReason.OK
    },
    "chart_min_y": {
        "value": "",
        "prompt": "Y(min)",
        "type": "decimal",
        "width": 0,
        "height": 0,
        "items": None,
        "events": False,
        "group": GROUP_NAME_CHART_PROPERTIES,
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "chart_max_y": {
        "value": "",
        "prompt": "Y(max)",
        "type": "decimal",
        "width": 0,
        "height": 0,
        "items": None,
        "events": False,
        "group": GROUP_NAME_CHART_PROPERTIES,
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
        "group": GROUP_NAME_CHART_PROPERTIES,
        "required": True,
        "valid": False,
        "reason": OptionReason.EMPTY
    },
    "chart_auto_scale": {
        "value": True,
        "prompt": "Automatic scaling",
        "type": "checkbox",
        "width": 0,
        "height": 0,
        "items": None,
        "events": False,
        "group": GROUP_NAME_CHART_PROPERTIES,
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
