import PySimpleGUI as sg
from ode_solver.gui.options import get_current_options, check_validity_of_all_options, capture_all_values


def options_select_file(window, _values):
    """
    Display a file selector to select the file containing the ODE function definition

    :param window: Calling window
    :param _values: Values read from calling window
    """
    # Hide the options dialog to make way for the file selection dialog, then show
    # the file selector
    window.disappear()
    filename = sg.popup_get_file("Function Definition",
                                 no_window=True,
                                 default_extension="py")
    window.reappear()

    # If the filename is specified, update the filename text box
    if filename:
        window["function_file"].Update(filename)
    return False


def options_clear_steps(window, values):
    """
    Clear the number of steps if the simulation duration is to be governed by
    a limit on the independent variable

    :param window: Calling window
    :param values: Values read from calling window
    """
    if values["limit"]:
        window["steps"].Update("")
    return False


def options_clear_limit(window, values):
    """
    Clear the independent variable limit if the simulation duration is to be governed by
    the number of steps

    :param window: Calling window
    :param values: Values read from calling window
    """
    if values["steps"]:
        window["limit"].Update("")
    return False


def options_ok(window, values):
    """
    Extract the values from the options dialog and store them

    :param window: Calling window
    :param values: Values read from calling window
    """
    # At this stage, we exclude empty values from the validation process - this gives the user
    # the option to set some then come back and set others later
    current_options = get_current_options()
    invalid_options = check_validity_of_all_options(current_options, True, window, values)
    if not invalid_options:
        capture_all_values(current_options, values)

    return not invalid_options


SIMULATION_OPTIONS_CALLBACKS = {
    "...": options_select_file,
    "OK": options_ok,
    "Cancel": None,
    "limit": options_clear_steps,
    "steps": options_clear_limit
}
