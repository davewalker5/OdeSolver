import FreeSimpleGUI as sg
import traceback
from ode_solver.cli.parser import load_simulation_from_args
from ode_solver.gui import RUN_SIMULATION_EVENT, CHART_EXPORT_KEY, DATA_EXPORT_KEY
from ode_solver.utils.data_exchange import check_export_format


def show_error_window(exception):
    """
    Show a window containing an error message and the call stack, based on a Python exception

    :param exception: Exception to show details for
    """
    error_text = "".join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    layout = [
        [sg.Text("A runtime error occurred:", font=("Any", 12, "bold"))],
        [sg.Multiline(
            error_text,
            size=(120, 25),
            font=("Courier New", 10),
            disabled=True,
            expand_x=True,
            expand_y=True,
            autoscroll=False,
        )],
        [sg.Button("Copy"), sg.Button("Close")]
    ]

    window = sg.Window(
        "ODE Solver Error",
        layout,
        modal=False,
        resizable=True,
        finalize=True,
    )

    while True:
        event, _ = window.read()
        if event in (sg.WIN_CLOSED, "Close"):
            break
        if event == "Copy":
            sg.clipboard_set(error_text)

    window.close()


def show_argument_error(message):
    """
    Show an argument processing error

    :param message: Error message
    """
    layout = [[sg.Text(message)], [sg.Button("Close")]]
    sg.Window("Invalid Arguments", layout, modal=True, keep_on_top=True, finalize=True).read(close=True)


def handle_args(args, window):
    """
    Handle command line arguments

    :param args: Parsed command line arguments and values
    """

    # Handle "no GUI"
    if args.no_gui:
        show_argument_error("The 'no GUI' flag is invalid in the current context")
        return False

    # Handle "normalise"
    if args.normalise:
        show_argument_error("The 'normalise' flag is invalid in the current context")
        return False

    # Load the simulation file, if specified
    if args.simulation:
        if not load_simulation_from_args(args.simulation):
            show_argument_error("Missing or invalid simulation file:\n{args.simulation}\n")
            return False

    # Handle the export flag
    if args.export:
        if not args.auto_run or not args.simulation:
            show_argument_error("A simulation file and auto-run must be specified to use export")
            return False

        # Check export to a supported type has been requested
        if not check_export_format(args.export):
            show_argument_error("Invalid export format specified")
            return False

    # Handle the charting flag
    if args.chart:
        if not args.auto_run or not args.simulation:
            show_argument_error("A simulation file and auto-run must be specified to export a chart")
            return False

    # Handle auto-run
    if args.auto_run:
        if not args.simulation:
            show_argument_error("A simulation file must be specified to use auto-run")
            return False

        window.write_event_value(RUN_SIMULATION_EVENT, {
            DATA_EXPORT_KEY: args.export,
            CHART_EXPORT_KEY: args.chart
        })

    return True


def run_event_loop(window, callbacks, args):
    """
    Run the main-window event loop

    :param window: Window for which to run the event loop
    :param callbacks: Dictionary of callback functions
    :param args: Parsed command line arguments and values
    """

    continue_loop = handle_args(args, window) if args else True
    while continue_loop:
        try:
            # Get the next event and if it's a window closed event then break out
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                break

            # Check to see if the event is in the callbacks. If not, it's ignored. Otherwise,
            # get the callback function. If it's none, break out. Otherwise, call the function
            if event in callbacks.keys():
                callback = callbacks[event]
                if callback:
                    exit_loop = callback(window, values)
                    if exit_loop:
                        break
                else:
                    break

        except Exception as exception:
            show_error_window(exception)

    window.close()
