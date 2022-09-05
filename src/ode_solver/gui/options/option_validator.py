import os
import PySimpleGUI as sg
from decimal import Decimal, InvalidOperation
from ode_solver.gui.options.option_reasons import OptionReason
from ode_solver.gui.options.option_definitions import get_current_options, get_values_from_current_options


def get_option_validity(name, display_name, option_type, required, new_value):
    """
    Given an option name and type and a new value for that option, return a dictionary of
    validity properties for that option and value

    :param name: Name of the option
    :param display_name: Display name of the option
    :param option_type: Type of the option
    :param required: Whether the parameter is mandatory
    :param new_value: Proposed new value for the option
    :return: Dictionary of validity information
    """
    validity = {
        "name": name,
        "display_name": display_name,
        "type": option_type,
        "required": required,
        "value": new_value,
        "valid": None,
        "reason": None
    }

    if option_type != "checkbox" and not new_value and required:
        validity["valid"] = False
        validity["reason"] = OptionReason.EMPTY
    elif option_type == "file":
        validity["valid"] = os.path.exists(new_value)
        validity["reason"] = OptionReason.OK if validity["valid"] else OptionReason.VALUE_ERROR
    elif option_type == "decimal":
        try:
            _ = Decimal(new_value)
            validity["valid"] = True
            validity["reason"] = OptionReason.OK
        except InvalidOperation:
            validity["valid"] = False
            validity["reason"] = OptionReason.VALUE_ERROR
    else:
        validity["valid"] = True
        validity["reason"] = OptionReason.OK

    return validity


def determine_basic_validity(options, ignore_empty_values, values):
    """
    Compile a list of options with invalid values, based purely on type and value with
    validity rules not applied

    :param options: Simulation option definitions dictionary
    :param ignore_empty_values: True to exclude empty values from validation
    :param values: Values read from calling window
    :return: List of invalid option dictionaries
    """
    invalid_options = []
    for key, value in values.items():
        # With a tab group in place, an additional key is present that isn't part of the
        # option list
        if key in options.keys():
            # Get the option properties
            option = options[key]

            # Get the validity
            validity = get_option_validity(key, option["prompt"], option["type"], option["required"], value)
            if not validity["valid"] and ((validity["reason"] != OptionReason.EMPTY) or not ignore_empty_values):
                invalid_options.append(validity)

    return invalid_options


def remove_invalid_option(invalid_options, option_name):
    """
    Removed a named option from an invalid options list but only if the reason it's there
    is that it's empty

    :param invalid_options: List of invalid option dictionaries
    :param option_name: Name of the option to remove
    """
    for i in range(len(invalid_options)):
        if invalid_options[i]["name"] == option_name:
            if invalid_options[i]["reason"] == OptionReason.EMPTY:
                del invalid_options[i]
            break


def apply_solution_limit_rules(invalid_options):
    """
    Apply rules regarding options affecting detection of the end of the simulation

    :param invalid_options: List of invalid option validity dictionaries
    """
    limit_validity = [v for v in invalid_options if v["name"] == "limit"]
    steps_validity = [v for v in invalid_options if v["name"] == "steps"]

    # If the limit is specified, the number of steps isn't required and vice versa
    if limit_validity and not steps_validity:
        remove_invalid_option(invalid_options, "limit")
    elif steps_validity and not limit_validity:
        remove_invalid_option(invalid_options, "steps")


def apply_chart_scaling_rules(invalid_options):
    """
    Apply chart scaling rules to a list of invalid options

    :param invalid_options: List of invalid option validity dictionaries
    """
    # If automatic scaling is being applied, none of the scaling properties are required
    remove_invalid_option(invalid_options, "chart_min_y")
    remove_invalid_option(invalid_options, "chart_max_y")
    remove_invalid_option(invalid_options, "chart_max_x")


def apply_validity_rules(step_adjustment, automatic_scaling, invalid_options):
    """
    Given a list of options that are invalid at a basic level (based on option
    type and value), apply validity rules to adjust the list

    :param step_adjustment: True if automatic step adjustment is enabled
    :param automatic_scaling: True if the chart is being scaled automatically
    :param invalid_options: List of invalid option validity dictionaries
    """
    apply_solution_limit_rules(invalid_options)

    # Tolerance is only required if step size adjustment is disabled
    if not step_adjustment:
        remove_invalid_option(invalid_options, "tolerance")

    if automatic_scaling:
        apply_chart_scaling_rules(invalid_options)


def highlight_invalid_options(options, invalid_options, window):
    """
    Highlight any invalid options in the options dialog

    :param options: Dictionary of option definitions
    :param invalid_options: List of invalid option dictionaries
    :param window: Calling window
    """
    invalid_option_keys = [o["name"] for o in invalid_options]
    all_text_boxes_keys = [k for k, v in options.items() if v["type"] not in ["list", "checkbox"]]
    for key in all_text_boxes_keys:
        colour = "pink" if key in invalid_option_keys else "white"
        window[key].update(background_color=colour)


def check_validity_of_all_options(options, ignore_empty_values, window, values):
    """
    Check the validity of all the options on the options dialog

    :param options: Simulation option definitions
    :param ignore_empty_values: True to exclude empty values from validation
    :param window: Calling window
    :param values: Values read from calling window
    :return: List of invalid options
    """
    invalid_options = determine_basic_validity(options, ignore_empty_values, values)
    step_adjustment = values["adjust_step_size"]
    automatic_scaling = values["chart_auto_scale"]
    apply_validity_rules(step_adjustment, automatic_scaling, invalid_options)
    if window:
        highlight_invalid_options(options, invalid_options, window)
    return invalid_options


def capture_all_values(simulation_options, values):
    """
    Copy the entered values to the simulation properties dictionary

    :param simulation_options: Simulation option properties and values dictionary
    :param values: Values read from calling window
    """
    for key, value in values.items():
        # With a tab group in place, an additional key is present that isn't part of the
        # option list
        if key in simulation_options:
            option = simulation_options[key]
            option["value"] = value


def pre_run_validate_options():
    """
    Validate the current options before starting a solution run

    :return: The current values if they're valid, otherwise None
    """
    # Get a dictionary of key:value pairs (excluding the menu configuration information)
    # and use this to check the validity of all values
    current_options = get_current_options()
    current_values = get_values_from_current_options()
    invalid_options = check_validity_of_all_options(current_options, False, None, current_values)
    valid = len(invalid_options) == 0
    if not valid:
        # Invalid parameters detected, so show a message box
        invalid_option_display_names = "\n".join([v["display_name"] for v in invalid_options])
        message = f"Invalid values for the following options:\n\n{invalid_option_display_names}\n"
        layout = [[sg.Text(message)], [sg.Button("Close")]]
        sg.Window("Invalid Options", layout, modal=True, keep_on_top=True, finalize=True).read(close=True)

    return current_values if valid else None
