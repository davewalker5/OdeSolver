import random
from pathlib import Path
from datetime import datetime

from seasonal.support.numeric import D, show_progress
from seasonal.support.calendar import circular_month_distance, month_range_around, random_month_in_range, \
    month_is_between
from seasonal.support.scoring import mse
from seasonal.support.solver import run_solver
from seasonal.support.csv import append_params_to_csv


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
