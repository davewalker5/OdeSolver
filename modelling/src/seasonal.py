import argparse
from pathlib import Path
from decimal import Decimal

from seasonal.fitting.seasonal import infer_search_space, fit, PARAMETER_COLUMNS
from seasonal.classification.seasonal import classify_seasonal_model_to_json
from seasonal.support.utils import D
from seasonal.support.solver import export_simulation
from modelling.src.seasonal.support.csv import load_and_normalise_observed_csv
from seasonal.support.consensus import write_consensus_parameters
from seasonal.support.synthesise import synthesise
from seasonal.support.tabulate import print_args_table, print_dict_table


def main():
    """
    Main entry point for the seasonal presence parameter fitter
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-sp", "--species", required="True", help="Species name")
    parser.add_argument("-o", "--observed", required=True, help="CSV file containing month,value columns")
    parser.add_argument("-s", "--simulation", required=True, help="Simulation JSON file for ODE Solver")
    parser.add_argument("-i", "--iterations", type=int, default=200, help="Number of parameter sets to test per run")
    parser.add_argument("-sc", "--solver-command", required=True, help="ODE Solver command")
    parser.add_argument("-c", "--csv", required=True, help="CSV file containing the accumulated data from multiple runs")
    parser.add_argument("-cj", "--consensus-json", required=True, help="JSON file to write the consensus parameters to")
    parser.add_argument("-cl", "--classification-json", required=True, help="JSON file to write the classification to")
    parser.add_argument("-esi", "--export-simulated", required=True, help="CSV file containing the simulated output")
    parser.add_argument("-psi", "--plot-simulated", required=True, help="PNG file containing the simulated chart")
    parser.add_argument("-esy", "--export-synthesised", required=True, help="CSV file containing the synthesised output")
    parser.add_argument("-psy", "--plot-synthesised", required=True, help="PNG file containing the synthesised chart")
    parser.add_argument("-sm", "--scale-method", choices=["least_squares", "max", "sum"], default="least_squares",
                        help="How to rescale the simulated shape onto the observed scale")
    parser.add_argument("-a", "--aggregation", choices=["mean", "max", "last"], default="mean",
                        help="How to convert the solver's sub-monthly output into monthly values")
    parser.add_argument("-r", "--round", action="store_true", help="Round synthesised values to integer counts")
    parser.add_argument("-tp", "--top-percent", type=Decimal, default=Decimal("20"),
                        help="Top percentage of rows to use in the consensus, sorted by SCORE")
    parser.add_argument("--active-threshold", default="0.05", help="Observed value threshold used to infer active months")
    parser.add_argument("--season-padding", default="1.0", help="Padding around inferred season start/end, in months")
    parser.add_argument("--peak-padding", default="1.5", help="Padding around observed peak month, in months")
    args = parser.parse_args()
    print_args_table(args, "Seasonal Presence Model Arguments")

    # Load the observed data and calculate the search space
    observed = load_and_normalise_observed_csv(args.observed)
    search_space = infer_search_space(observed, D(str(args.active_threshold)), D(str(args.season_padding)),
                                      D(str(args.peak_padding)))
    print_dict_table(search_space, "Inferred Search Space")

    # Generate the parameter fitting CSV
    print()
    fit(args.observed,
        args.csv,
        observed,
        Path(args.simulation),
        args.iterations,
        args.solver_command,
        search_space)

    # Write the consensus parameter set
    consensus = write_consensus_parameters(args.csv, args.consensus_json, args.species, PARAMETER_COLUMNS, args.top_percent)

    # Classify the consensus parameter set
    classify_seasonal_model_to_json(consensus, args.classification_json)

    # Run the solution using the consensus parameters and export the simulated results CSV and chart
    export_simulation(args.solver_command, args.consensus_json, args.simulation, args.export_simulated, args.plot_simulated)

    # Generate the synthesised data
    synthesise(args.species, args.observed, args.export_simulated, args.export_synthesised, args.plot_synthesised,
               args.scale_method, args.aggregation, args.round)


if __name__ == "__main__":
    main()
