import json
import PySimpleGUI as sg


def save_options(simulation_options):
    """
    Write an options file: This is a JSON dump of the specified options

    :param simulation_options: Options to save
    """
    filename = sg.popup_get_file("Options File",
                                 save_as=True,
                                 no_window=True,
                                 default_extension="json")
    if filename:
        with open(filename, mode="wt", encoding="utf-8") as json_f:
            json.dump(simulation_options, json_f, indent=4)


def load_options():
    """
    Load an options file
    """
    filename = sg.popup_get_file("Options File",
                                 no_window=True,
                                 default_extension="json")
    if filename:
        with open(filename, mode="rt", encoding="utf-8") as json_f:
            simulation_options = json.load(json_f)
    else:
        simulation_options = None

    return simulation_options
