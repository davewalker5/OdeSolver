import argparse
from ode_solver import PROGRAM_NAME, PROGRAM_DESCRIPTION
from ode_solver.utils.version import get_application_version
from ode_solver.options.options_io import load_simulation_options
from ode_solver.options.option_definitions import set_current_options_from_values

NORMALISE_TRUE = ["true", "yes", "y", "1"]
NORMALISE_FALSE = ["false", "no", "n", "0"]


def parse():
    version = get_application_version()
    parser = argparse.ArgumentParser(
        prog=f"{PROGRAM_NAME} v{version}",
        description=PROGRAM_DESCRIPTION
    )

    parser.add_argument("-s", "--simulation", help="Input simulation file path")
    parser.add_argument("-e", "--export", help="Export file path (CSV, JSON or XML)")
    parser.add_argument("-c", "--chart", help="Chart file path")
    parser.add_argument("-ar", "--auto-run", action="store_true", help="Automatically run the specified")
    parser.add_argument("-ng", "--no-gui", action="store_true", help="Suppress the UI")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress output of results to the console in CLI mode")
    parser.add_argument("-n", "--normalise", type=str.lower, choices=NORMALISE_TRUE + NORMALISE_FALSE,
                        help="Set the normalisation flag in the simulation options")
    args = parser.parse_args()

    return args


def load_simulation_from_args(file_path):
    """
    Load a simulation definition, if specified on the command line

    :param args: Parsed command line arguments and values
    """
    try:
        simulation_options = load_simulation_options(file_path)
        set_current_options_from_values(simulation_options)
    except FileNotFoundError:
        return False

    return True
