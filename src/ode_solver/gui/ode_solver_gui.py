from ode_solver.gui.menus import get_menu_definition, get_menu_callbacks
from ode_solver.gui.windows import create_main_window, run_event_loop


def main():
    """
    Main method to create the ODE solver GUI
    """
    menu_definition = get_menu_definition()
    menu_callbacks = get_menu_callbacks()
    window = create_main_window(menu_definition)
    run_event_loop(window, menu_callbacks)


if __name__ == "__main__":
    main()
