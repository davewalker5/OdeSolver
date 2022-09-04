from ode_solver.gui.menus.file_menu_callbacks import FILE_MENU_DEFINITION
from ode_solver.gui.menus.simulation_menu_callbacks import SIMULATION_MENU_DEFINITION

MENU = {
    "&File": FILE_MENU_DEFINITION,
    "&Simulation": SIMULATION_MENU_DEFINITION
}


def get_menu_definition():
    """
    Build the list of menu and sub-menu option names to configure the menu bar
    """
    definition = []
    for menu_name in MENU.keys():
        option_list = []
        for option_name, option_definition in MENU[menu_name].items():
            option_list.append(option_name)
            if type(option_definition) == dict:
                option_list.append(list(option_definition.keys()))
        definition.append([menu_name, option_list])

    return definition


def add_callbacks(menu_definition, callbacks):
    """
    Find menu options associated with function callbacks in a menu definition and add
    a mapping between the option name and callback to the callbacks

    :param menu_definition: Dictionary of menu definitions
    :param callbacks: Dictionary of callbacks to add the mappings to
    """
    for option_name, option_definition in menu_definition.items():
        option_type = type(option_definition)
        if option_type == dict:
            add_callbacks(option_definition, callbacks)
        elif option_type:
            callbacks[option_name.replace("&", "")] = option_definition


def get_menu_callbacks():
    """
    Return all the mappings between menu option names and callback functions

    :return: Dictionary of option name/callback mappings
    """
    callbacks = {}
    add_callbacks(MENU, callbacks)
    return callbacks
