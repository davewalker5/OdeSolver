from ode_solver.options.option_validator import check_validity_of_all_options


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


def validate_all_options(options, ignore_empty_values, window, values):
    """
    Check the validity of all the options on the options dialog

    :param options: Simulation option definitions
    :param ignore_empty_values: True to exclude empty values from validation
    :param window: Calling window
    :param values: Values read from calling window
    :return: List of invalid options
    """
    invalid_options = check_validity_of_all_options(options, ignore_empty_values, values)
    if window:
        highlight_invalid_options(options, invalid_options, window)
    return invalid_options
