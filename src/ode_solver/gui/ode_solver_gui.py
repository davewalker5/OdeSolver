from ode_solver.gui.menus.menu_configuration import get_menu_definition, get_menu_callbacks
from ode_solver.gui.windows.window_layout import create_main_window
from ode_solver.gui.windows.event_loop import run_event_loop
from ode_solver.cli.parser import parse


def gui_main(args):
    """
    Main method to create the ODE solver GUI
    """
    menu_definition = get_menu_definition()
    menu_callbacks = get_menu_callbacks()
    window = create_main_window(menu_definition)
    run_event_loop(window, menu_callbacks, args)


if __name__ == "__main__":
    gui_main(parse())
