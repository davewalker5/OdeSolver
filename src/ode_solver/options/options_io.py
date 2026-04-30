import json


def save_simulation_options(simulation_options, file_path):
    """
    Write an options file: This is a JSON dump of the specified options

    :param simulation_options: Options to save
    :param file_path: Path to the options file to write (JSON format)
    """
    with open(file_path, mode="wt", encoding="utf-8") as json_f:
        json.dump(simulation_options, json_f, indent=4)


def load_simulation_options(file_path):
    """
    Load an options file

    :param file_path: Path to the options file (JSON format)
    """
    with open(file_path, mode="rt", encoding="utf-8") as json_f:
        simulation_options = json.load(json_f)
    return simulation_options
