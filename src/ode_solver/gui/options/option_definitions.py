from ode_solver.gui.options.integration_methods import IntegrationMethods

SIMULATION_OPTIONS = {
    "function_file": {
        "value": "",
        "prompt": "Function file",
        "type": "file",
        "items": None,
        "events": False,
        "group": "Simulation Parameters",
        "valid": False,
        "reason": None
    },
    "method": {
        "value": "",
        "prompt": "Method",
        "type": "list",
        "items": IntegrationMethods.method_name_list(),
        "events": False,
        "group": "Simulation Parameters",
        "valid": False,
        "reason": None
    },
    "limit": {
        "value": "",
        "prompt": "Limit of x",
        "type": "decimal",
        "items": None,
        "events": True,
        "group": "Simulation Parameters",
        "valid": False,
        "reason": None
    },
    "steps": {
        "value": "",
        "prompt": "No. steps",
        "type": "decimal",
        "items": None,
        "events": True,
        "group": "Simulation Parameters",
        "valid": False,
        "reason": None
    },
    "step_size": {
        "value": "",
        "prompt": "Initial step size",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Simulation Parameters",
        "valid": False,
        "reason": None
    },
    "initial_value": {
        "value": "",
        "prompt": "Initial y",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Simulation Parameters",
        "valid": False,
        "reason": None
    },
    "tolerance": {
        "value": "",
        "prompt": "Tolerance",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Step Adjustment",
        "valid": False,
        "reason": None
    },
    "adjust_step_size": {
        "value": False,
        "prompt": "Adjust step size",
        "type": "checkbox",
        "items": None,
        "events": False,
        "group": "Step Adjustment",
        "valid": False,
        "reason": None
    },
    "chart_title": {
        "value": "",
        "prompt": "Title",
        "type": "text",
        "items": None,
        "events": False,
        "group": "Chart Properties",
        "valid": True,
        "reason": None
    },
    "chart_min_y": {
        "value": "0",
        "prompt": "Y(min)",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Chart Properties",
        "valid": True,
        "reason": None
    },
    "chart_max_y": {
        "value": "",
        "prompt": "Y(max)",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Chart Properties",
        "valid": False,
        "reason": None
    },
    "chart_max_x": {
        "value": "",
        "prompt": "X(max)",
        "type": "decimal",
        "items": None,
        "events": False,
        "group": "Chart Properties",
        "valid": False,
        "reason": None
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
