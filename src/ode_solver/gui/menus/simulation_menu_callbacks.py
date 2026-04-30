from ode_solver.gui.windows.window_layout import create_options_dialog
from ode_solver.gui.windows.event_loop import run_event_loop
from ode_solver.options.option_definitions import get_current_options
from ode_solver.gui.options.option_validator import validate_options_pre_run
from ode_solver.gui.menus.options_dialog_callbacks import SIMULATION_OPTIONS_CALLBACKS
from ode_solver.gui.runner.solution_runner import SolutionRunner
from ode_solver.gui.runner.solution_chart import SolutionChart
from ode_solver.gui import RUN_SIMULATION_EVENT, CHART_EXPORT_KEY, DATA_EXPORT_KEY
from ode_solver.utils.data_exchange import write_simulation
from ode_solver.utils.chart import export_chart


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


def menu_run(window, event_values):
    """
    Start a simulation with the current simulation properties

    :param window: Calling window
    :param event_values: Event values read from calling window
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

        # Handle post-run data and chart export
        if isinstance(event_values, dict) and RUN_SIMULATION_EVENT in event_values.keys():
            # Data export
            export_file = event_values[RUN_SIMULATION_EVENT][DATA_EXPORT_KEY]
            if export_file:
                write_simulation(solution_runner.history, export_file)

            # Chart export
            chart_file = event_values[RUN_SIMULATION_EVENT][CHART_EXPORT_KEY]
            if chart_file:
                export_chart(solution_runner.history, chart_file, values)

    return False


SIMULATION_MENU_DEFINITION = {
    "Options": menu_options,
    "Run": menu_run
}
