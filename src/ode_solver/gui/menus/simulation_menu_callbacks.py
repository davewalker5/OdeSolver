from ode_solver.gui.windows.window_layout import create_options_dialog
from ode_solver.gui.windows.event_loop import run_event_loop
from ode_solver.options.option_definitions import get_current_options
from ode_solver.gui.options.option_validator import validate_options_pre_run
from ode_solver.gui.menus.options_dialog_callbacks import SIMULATION_OPTIONS_CALLBACKS
from ode_solver.gui.runner.solution_runner import SolutionRunner
from ode_solver.gui.runner.solution_chart import SolutionChart

solution_chart = None
solution_runner = None


def get_history():
    """
    Return the history for the latest run or None if there is no run

    :return: List of dictionaries containing the points in the solution
    """
    return solution_runner.history if solution_runner else None


def menu_options(_window, _values):
    """
    Create and show the simulation options dialog

    :param _window: Calling window
    :param _values: Values read from calling window
    """
    simulation_options = get_current_options()
    dialog = create_options_dialog(simulation_options)
    run_event_loop(dialog, SIMULATION_OPTIONS_CALLBACKS, None)
    return False


def menu_run(window, _values):
    """
    Start a simulation with the current simulation properties

    :param window: Calling window
    :param _values: Values read from calling window
    """
    global solution_chart, solution_runner

    values = validate_options_pre_run()
    if values:
        # Create a charting instance that integrates Matplotlib with FreeSimpleGUI canvas
        if solution_chart is None:
            solution_chart = SolutionChart(window["chart"])

        if solution_runner is None:
            solution_runner = SolutionRunner(solution_chart, window["table"], window)

        # Initialise the axes with the new values and run the solution
        solution_chart.initialise_chart(values)
        solution_runner.run(values)
    return False


SIMULATION_MENU_DEFINITION = {
    "Options": menu_options,
    "Run": menu_run
}
