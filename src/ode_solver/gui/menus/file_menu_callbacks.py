import PySimpleGUI as sg
from ode_solver.gui.options import get_values_from_current_options, \
    set_current_options_from_values, save_options, load_options
from ode_solver.gui.menus.simulation_menu_callbacks import get_history
from ode_solver.utils import write_csv, write_json, write_xml


def menu_save_options(_window, _values):
    """
    Show a file selection dialog and save the current simulation options to the selected file
    """
    simulation_options = get_values_from_current_options()
    save_options(simulation_options)
    return False


def menu_load_options(_window, _values):
    """
    Show a file selection dialog and load the simulation options from the selected file
    """
    simulation_options = load_options()
    set_current_options_from_values(simulation_options)
    return False


def export_results(extension):
    """
    Export the results of the latest solution run to a file

    :param extension: Extension of the file, giving the file type
    """
    # Map file extensions to the appropriate writer
    writer_methods = {
        "csv": write_csv,
        "json": write_json,
        "xml": write_xml
    }

    # Get the solution history. If there is one, prompt for a filename and if one is selected
    # write the history to the file
    history = get_history()
    if history:
        filepath = sg.popup_get_file("Results File",
                                     save_as=True,
                                     no_window=True,
                                     default_extension=extension)
        if filepath:
            writer_methods[extension.casefold()](history, filepath)
    else:
        message = "You must run a solution to save the solution history"
        layout = [[sg.Text(message)]]
        sg.Window("No Solution History", layout, modal=True, keep_on_top=True, finalize=True).read(close=True)


def menu_export_csv(_window, _values):
    """
    Export the solution history from the last run to a CSV file

    :param _window: Calling window
    :param _values: Values read from calling window
    """
    export_results("csv")
    return False


def menu_export_json(_window, _values):
    """
    Export the solution history from the last run to a JSON file

    :param _window: Calling window
    :param _values: Values read from calling window
    """
    export_results("json")
    return False


def menu_export_xml(_window, _values):
    """
    Export the solution history from the last run to an XML file

    :param _window: Calling window
    :param _values: Values read from calling window
    """
    export_results("xml")
    return False


FILE_MENU_DEFINITION = {
    "&Save": menu_save_options,
    "&Load": menu_load_options,
    "&Export": {
        "CSV": menu_export_csv,
        "JSON": menu_export_json,
        "XML:": menu_export_xml
    },
    "---": None,
    "E&xit": None
}
