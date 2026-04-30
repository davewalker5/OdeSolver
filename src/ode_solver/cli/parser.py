import argparse
from ode_solver import PROGRAM_NAME, PROGRAM_DESCRIPTION
from ode_solver.utils import get_application_version


def main():
    version = get_application_version()
    parser = argparse.ArgumentParser(
        prog=f"{PROGRAM_NAME} v{version}",
        description=PROGRAM_DESCRIPTION
    )

    parser.add_argument("-s", "--simulation", help="Input simulation file path")
    parser.add_argument("-e", "--export", help="Export file path (CSV, JSON or XML)")
    parser.add_argument("-c", "--chart", help="Chart file path")
    parser.add_argument("-a", "--auto-run", action="store_true", help="Automatically run the specified")
    parser.add_argument("-ng", "--nogui", action="store_true", help="Suppress the UI")
    args = parser.parse_args()

    return args
