import argparse
import random
import sys
from pathlib import Path
from datetime import datetime
from decimal import Decimal

from fitting.utils import D, show_progress
from fitting.calendar import circular_month_distance, month_range_around, random_month_in_range, month_is_between, random_month_in_range
from fitting.scoring import mse
from fitting.solver import run_solver, export_simulation
from fitting.io import append_params_to_csv, load_and_normalise_observed_csv
from fitting.consensus import write_consensus_parameters
from fitting.synthesise import synthesise
from fitting.tabulate import print_args_table, print_dict_table


PARAMETER_COLUMNS = [
    "TIMESTAMP",
    "OBSERVED",
    "GROWTH",
    "DECAY",
    "OOS_DECAY",
    "POST_PEAK_DECAY",
    "POST_PEAK_SHARPNESS",
    "SEASON_START",
    "SEASON_END",
    "SHARPNESS",
    "FORCING_PEAK",
    "SCORE",
    "WRAPS_YEAR",
]


def infer_active_season(observed, threshold=D("0.05")):
    """
    Infer the active season from observed monthly values.

    The method treats the year as circular and finds the largest gap between
    active months. The active season is then assumed to begin after that gap and
    end before it. This works for both summer visitors and winter visitors.

    :param observed: Dictionary of observed monthly values
    :param threshold: Values above this are considered active
    :return: Dictionary describing the inferred active season
    """
    active = sorted(m for m, v in observed.items() if v > threshold)

    if not active:
        raise ValueError("No active months detected in observed data")

    # If the species appears active in every month, there is no bounded seasonal
    # presence window. This fitter is probably the wrong model for that case.
    if len(active) == 12:
        raise ValueError(
            "Observed data is active in every month; use the resident detectability model instead"
        )

    # Find the largest circular gap between active months.
    gaps = []
    for i, month in enumerate(active):
        next_month = active[(i + 1) % len(active)]
        gap = (next_month - month) % 12
        if gap == 0:
            gap = 12
        gaps.append((gap, month, next_month))

    _, gap_start, gap_end = max(gaps)

    season_start = D(gap_end)
    season_end = D(gap_start)
    peak_month = D(max(observed, key=observed.get))
    wraps_year = season_start > season_end

    return {
        "active_months": active,
        "season_start_centre": season_start,
        "season_end_centre": season_end,
        "forcing_peak_centre": peak_month,
        "wraps_year": wraps_year,
    }


def infer_search_space(observed, threshold=D("0.05"), padding=D("1.0"), peak_padding=D("1.5")):
    """
    Infer biologically plausible random-search bounds from the observed data.

    This does not force the fitted curve to match the observations. It only
    constrains the random search to a plausible seasonal region, making fitted
    parameters more interpretable and allowing winter seasons to wrap across the
    end of the year.

    :param observed: Dictionary of observed monthly values
    :param threshold: Values above this are treated as active
    :param padding: Padding around inferred season start/end
    :param peak_padding: Padding around observed peak month
    :return: Dictionary describing the random search space
    """
    inferred = infer_active_season(observed, threshold)

    start_range = month_range_around(inferred["season_start_centre"], padding)
    end_range = month_range_around(inferred["season_end_centre"], padding)
    peak_range = month_range_around(inferred["forcing_peak_centre"], peak_padding)

    return {
        **inferred,
        "threshold": threshold,
        "padding": padding,
        "peak_padding": peak_padding,
        "season_start_range": start_range,
        "season_end_range": end_range,
        "forcing_peak_range": peak_range,
    }


def weighted_score(observed, simulated):
    """
    Combine the following error components to produce a single weighted error score:

    - Curve fit error
    - Peak month error
    - First/last active month error

    The seasonal boundary errors are calculated using circular year logic, so they
    work for both normal seasons, e.g. April..August, and wrapped seasons, e.g.
    October..March.

    :param observed: Dictionary of observed data points
    :param simulated: Dictionary of simulated data points
    :return: Weighted error score
    """

    # Calculate the MSE across the curve
    curve_error = mse(observed, simulated)

    # Determine the observed and simulated peaks and calculate the peak error
    observed_peak = max(observed, key=observed.get)
    simulated_peak = max(simulated, key=simulated.get)
    peak_error = circular_month_distance(observed_peak, simulated_peak) / D("12")

    try:
        observed_season = infer_active_season(observed)
        simulated_season = infer_active_season(simulated)

        start_error = circular_month_distance(
            observed_season["season_start_centre"],
            simulated_season["season_start_centre"],
        ) / D("12")

        end_error = circular_month_distance(
            observed_season["season_end_centre"],
            simulated_season["season_end_centre"],
        ) / D("12")

    except ValueError:
        start_error = D("1")
        end_error = D("1")

    # Calculate a weighted sum of the error components. Errors in the shape of the curve
    # have a weighting of 1.0, other components of 0.25. This cares most about the shape
    # of the curve but does penalise if the seasonality is wrong
    return curve_error + D("0.25") * peak_error + D("0.25") * start_error + D("0.25") * end_error


def make_random_params(search_space):
    """
    Generate a random set of parameters for the seasonal model.

    The random ranges are inferred from the observed data, allowing the fitter to
    handle both summer visitors and winter visitors. For winter visitors, season
    start/end can wrap across the end of the year, e.g. October..March.

    :param search_space: Search space inferred from observed data
    :return: Dictionary of parameter values
    """
    season_start = random_month_in_range(*search_space["season_start_range"])
    season_end = random_month_in_range(*search_space["season_end_range"])

    # Choose a forcing peak close to the observed peak, but require it to sit
    # inside the generated season window. If repeated attempts fail, fall back to
    # a random month within the generated season window.
    forcing_peak = None
    for _ in range(20):
        candidate = random_month_in_range(*search_space["forcing_peak_range"])
        if month_is_between(candidate, season_start, season_end):
            forcing_peak = candidate
            break

    if forcing_peak is None:
        forcing_peak = random_month_in_range(season_start, season_end)

    return {
        "GROWTH": str(round(random.uniform(1.0, 5.0), 3)),
        "DECAY": str(round(random.uniform(0.5, 3.0), 3)),
        "OOS_DECAY": str(round(random.uniform(1.0, 8.0), 3)),
        "POST_PEAK_DECAY": str(round(random.uniform(0.0, 8.0), 3)),
        "POST_PEAK_SHARPNESS": str(round(random.uniform(1.0, 10.0), 3)),
        "SEASON_START": str(season_start),
        "SEASON_END": str(season_end),
        "SHARPNESS": str(round(random.uniform(1.0, 15.0), 3)),
        "FORCING_PEAK": str(forcing_peak),
    }

def fit(observed_csv,
        parameters_csv,
        observed,
        simulation_file,
        iterations,
        solver_command,
        search_space):
    """
    Parameter fitting loop
    
    :param observed_csv: Path to the observed data file
    :param parameters_csv: Path to the output parameters CSV file
    :param observed: Observed behaviour being matched
    :param simulation_file: Path to the ODE Solver simulation file
    :param iterations: Number of iterations in the fit
    :param solver_command: Command used to run the ODE Solver
    :param search_space: Search space for random parameter generation
    """

    for i in range(iterations):
        show_progress(i, iterations)

        # Generate a random parameter set
        params = make_random_params(search_space)

        try:
            # Run the simulation and score the match
            simulated = run_solver(simulation_file, params, solver_command)
            score = weighted_score(observed, simulated)

            params["TIMESTAMP"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            params["OBSERVED"] = Path(observed_csv).name
            params["SCORE"] = str(score)

            append_params_to_csv(params, PARAMETER_COLUMNS, parameters_csv)

        except Exception as e:
            print(f"Trial {i + 1}: failed: {e}")
            continue


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
    parser.add_argument("-esi", "--export-simulated", required=True, help="CSV file containing the simulated output")
    parser.add_argument("-psi", "--plot-simulated", required=True, help="PNG file containing the simulated chart")
    parser.add_argument("-esy", "--export-synthesised", required=True, help="CSV file containing the synthesised output")
    parser.add_argument("-psy", "--plot-synthesised", required=True, help="PNG file containing the synthesised chart")
    parser.add_argument("-sm", "--scale-method", choices=["least_squares", "max", "sum"], default="least_squares", help="How to rescale the simulated shape onto the observed scale")
    parser.add_argument("-a", "--aggregation", choices=["mean", "max", "last"], default="mean", help="How to convert the solver's sub-monthly output into monthly values")
    parser.add_argument("-r", "--round", action="store_true", help="Round synthesised values to integer counts")
    parser.add_argument("-tp", "--top-percent", type=Decimal, default=Decimal("20"), help="Top percentage of rows to use in the consensus, sorted by SCORE")
    parser.add_argument("--active-threshold", default="0.05", help="Observed value threshold used to infer active months")
    parser.add_argument("--season-padding", default="1.0", help="Padding around inferred season start/end, in months")
    parser.add_argument("--peak-padding", default="1.5", help="Padding around observed peak month, in months")
    args = parser.parse_args()
    print_args_table(args, "Seasonal Presence Model Arguments")

    # Load the observed data and calculate the search space
    observed = load_and_normalise_observed_csv(args.observed)
    search_space = infer_search_space(observed, D(str(args.active_threshold)), D(str(args.season_padding)), D(str(args.peak_padding)))
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
    write_consensus_parameters(args.csv, args.consensus_json, args.species, PARAMETER_COLUMNS, args.top_percent)

    # Run the solution using the consensus parameters and export the simulated results CSV and chart
    export_simulation(args.solver_command, args.consensus_json, args.simulation, args.export_simulated, args.plot_simulated)

    # Generate the synthesised data
    synthesise(args.species, args.observed, args.export_simulated, args.export_synthesised, args.plot_synthesised, args.scale_method, args.aggregation, args.round)


if __name__ == "__main__":
    main()
