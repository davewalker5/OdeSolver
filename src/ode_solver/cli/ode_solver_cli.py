from datetime import datetime
from ode_solver.cli.parser import parse, load_simulation_from_args, NORMALISE_TRUE
from ode_solver.utils.data_exchange import check_export_format
from ode_solver.options.option_validator import pre_run_validate_options
from ode_solver.cli.solution_runner import SolutionRunner
from ode_solver.utils.data_exchange import write_simulation
from ode_solver.utils.chart import export_chart


def print_error(message):
    """
    Show an argument processing error

    :param message: Error message
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} : ERROR : {message}")


def handle_args(args):
    """
    Handle command line arguments

    :param args: Parsed command line arguments and values
    """

    # Load the simulation file
    if not args.simulation:
            print_error(f"A simulation file is required to run the ODE Solver from the command line")
            return False

    if not load_simulation_from_args(args.simulation):
        print_error(f"Missing or invalid simulation file:\n{args.simulation}\n")
        return False

    # Handle the export flag
    if args.export:
        if not args.simulation:
            print_error(f"A simulation file must be specified to use export")
            return False

        # Check export to a supported type has been requested
        if not check_export_format(args.export):
            print_error(f"Invalid export format specified")
            return False

    # Handle the charting flag
    if args.chart:
        if not args.simulation:
            print_error(f"A simulation file must be specified to export a chart")
            return False

    return True
    

def cli_main(args):
    """
    Main method to run the ODE solver from the command line

    :param args: Parsed command line arguments and values
    """

    # Validate the command line arguments
    if not handle_args(args):
        return

    # Validate the options
    simulation_options, invalid_options = pre_run_validate_options()
    if len(invalid_options) > 0:
        for o in invalid_options:
            print_error(f"Invalid value for '{o['display_name']}' : '{o['value']}'")
            return

    # Run the solution
    solution_runner = SolutionRunner(args.quiet)
    solution_runner.run(simulation_options)

    # Override the simulation's normalisation option, if the normalisation flag has been
    # supplied
    if args.normalise:
        simulation_options["normalise"] = args.normalise in NORMALISE_TRUE

    # If requested, normalise the data
    if simulation_options["normalise"]:
        solution_runner.normalise()

    # Data export
    if args.export:
        write_simulation(solution_runner.history, args.export)

    # Chart export
    if args.chart:
        export_chart(solution_runner.history, args.chart, simulation_options)


if __name__ == "__main__":
    cli_main(parse())
