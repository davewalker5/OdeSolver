import FreeSimpleGUI as sg
from ode_solver.options.options_io import load_simulation_options, save_simulation_options


def save_options(simulation_options):
    """
    Write an options file: This is a JSON dump of the specified options

    :param simulation_options: Options to save
    """
    file_path = sg.popup_get_file("Options File",
                                 save_as=True,
                                 no_window=True,
                                 default_extension="json")
    if file_path:
        save_simulation_options(simulation_options, file_path)


def load_options():
    """
    Load an options file
    """
    file_path = sg.popup_get_file("Options File",
                                 no_window=True,
                                 default_extension="json")
    if file_path:
        simulation_options = load_simulation_options(file_path)
    else:
        simulation_options = None

    return simulation_options
