import argparse
import csv
import json
import os
import random
import subprocess
import tempfile
import sys
from decimal import Decimal
from pathlib import Path
from datetime import datetime


def D(value):
    """
    Safely convert a value to a Decimal

    :param value: Value to convert
    :return: The Decimal conversion of that value
    """
    return Decimal(str(value))


def circular_month_distance(a, b):
    """
    Calculate the shortest distance between two month-like values on a circular year.

    :param a: First month
    :param b: Second month
    :return: Shortest distance in months
    """
    a = D(a)
    b = D(b)
    diff = abs(a - b)
    return min(diff, D("12") - diff)


def wrap_month(value):
    """
    Wrap a month-like value into the range 1..12.

    This allows random search ranges to cross the year boundary. For example,
    12.5 becomes 0.5 months into the next year, represented as 0.5 + 12 -> 12.5
    during calculation and then wrapped back to 1..12 when stored.

    :param value: Month-like value
    :return: Month-like Decimal in the range 1..12
    """
    value = D(value)

    while value < D("1"):
        value += D("12")

    while value > D("12"):
        value -= D("12")

    return value


def month_range_around(centre, padding):
    """
    Create a circular month range around a centre month.

    The result may wrap across the year boundary. For example, centre 1 with
    padding 2 gives the range 11..3.

    :param centre: Centre month
    :param padding: Padding either side, in months
    :return: Tuple of low, high month bounds
    """
    return wrap_month(D(centre) - D(padding)), wrap_month(D(centre) + D(padding))


def random_month_in_range(low, high):
    """
    Select a random Decimal month from a possibly wrapped range.

    Examples:
    - 4..8 means April to August
    - 10..3 means October to March, crossing the end of the year

    :param low: Lower bound
    :param high: Upper bound
    :return: Random month-like Decimal in the range 1..12
    """
    low = D(low)
    high = D(high)

    if low <= high:
        return D(round(random.uniform(float(low), float(high)), 2))

    # Wrapped range, e.g. 10..3. Choose from 10..12 or 1..3, weighted by length.
    late_length = D("12") - low
    early_length = high - D("1")
    total_length = late_length + early_length

    if total_length <= 0:
        return wrap_month(low)

    if D(str(random.random())) < late_length / total_length:
        return D(round(random.uniform(float(low), 12.0), 2))

    return D(round(random.uniform(1.0, float(high)), 2))


def month_is_between(month, start, end):
    """
    Test whether a month sits inside a possibly wrapped seasonal window.

    :param month: Month to test
    :param start: Season start
    :param end: Season end
    :return: True if the month is inside the window
    """
    month = D(month)
    start = D(start)
    end = D(end)

    if start <= end:
        return start <= month <= end

    return month >= start or month <= end


def random_month_between(start, end):
    """
    Pick a random month inside a possibly wrapped seasonal window.

    :param start: Season start
    :param end: Season end
    :return: Random month-like Decimal
    """
    return random_month_in_range(start, end)


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


def format_search_space(search_space):
    """
    Format a search space for readable console output.

    :param search_space: Search space dictionary
    :return: Multi-line string
    """
    def fmt_range(r):
        return f"{r[0]}..{r[1]}"

    return "\n".join([
        "Inferred search space",
        "---------------------",
        f"Active months:       {search_space['active_months']}",
        f"Wraps year:          {search_space['wraps_year']}",
        f"Season start centre: {search_space['season_start_centre']}",
        f"Season end centre:   {search_space['season_end_centre']}",
        f"Forcing peak centre: {search_space['forcing_peak_centre']}",
        f"Season start range:  {fmt_range(search_space['season_start_range'])}",
        f"Season end range:    {fmt_range(search_space['season_end_range'])}",
        f"Forcing peak range:  {fmt_range(search_space['forcing_peak_range'])}",
        "\n"
    ])


def load_observed_csv(path):
    """
    Load the observed data and normalise it, mapping it into the range 0 to 1.0. The
    CSV file is expected to have:

    - A "month" column containing the month number
    - A "value" column containing the presence score or raw count
    - 12 records, one for each month (1 to 12)

    :param path: Path to the CSV file to load
    :return: Normalised observed data
    """

    # Load the observed data
    rows = {}

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = int(row["month"])
            value = D(row["value"])
            rows[month] = value

    # Calculate the maximum
    max_value = max(rows.values())

    # If the data is flat, at 0.0, avoid divide-by-zero and return a "zero" data set
    if max_value == 0:
        return {m: D("0") for m in rows}

    # Normalise the data
    return {
        month: value / max_value
        for month, value in rows.items()
    }


def load_simulated_json(path):
    """
    Load the JSON format simulation output

    :param path: Path to the simulation output file
    :return: A list of dictionaries, each representing a point (t, y)
    """

    # Load the data
    with open(path) as f:
        data = json.load(f)

    # Compile a list of points in which y is the normalised value, if present, or the
    # non-normalised value if not
    points = []
    for p in data:
        y_key = "y_normalised" if "y_normalised" in p else "y"

        points.append({
            "t": D(p["t"]),
            "y": D(p[y_key]),
        })

    return points


def monthly_average(points):
    """
    Converts the points representing the solution into monthly bins

    t = 0.0..0.999 -> month 1
    t = 1.0..1.999 -> month 2
    ...
    t = 11.0..11.999 -> month 12

    :param points: List of dictionaries, each representing a point in the solution
    :return: A dictionary of values binned by month
    """

    bins = {m: [] for m in range(1, 13)}

    for p in points:
        month = int(p["t"]) + 1

        if 1 <= month <= 12:
            bins[month].append(p["y"])

    return {
        month: sum(values) / len(values)
        for month, values in bins.items()
        if values
    }


def mse(observed, simulated):
    """
    Calculate the mean squared error (MSE) between observed and simulated data

    MSE = (1 / N) * Σ (observed - simulated)²

    :param observed: Dictionary of observed data points
    :param simulated: Dictionary of simulated data points
    :return: MSE
    """
    # Get a list of months that appear in both the observed and simulated data
    months = sorted(set(observed) & set(simulated))
    if not months:
        raise ValueError("No overlapping months between observed and simulated data")

    # For each month, the error is calculated as the squared difference between observed
    # and simulated data. This is summed to give the mismatch across the year and then
    # divided by the number of months to give a monthly average mismatch
    return sum((observed[m] - simulated[m]) ** 2 for m in months) / D(len(months))


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

def run_solver(simulation_file, params, solver_command):
    """
    Run the solution with the current set of parameters
    
    :param simulation_file: Path to the ODE Solver simulation file
    :param params: Dictionary of seasonal presence parameters
    :param solver_command: Command used to run the ODE Solver
    :param search_space: Search space inferred from observed data
    :return: A dictionary of values binned by month
    """
    with tempfile.TemporaryDirectory() as tmp:
        # Generate the file path
        tmp = Path(tmp)
        params_file = tmp / "seasonal_params.json"
        output_file = tmp / "output.json"

        # Write the parameters to a temporary JSON file
        params_file.write_text(json.dumps(params, indent=2))

        # Set the environment variable that points to the parameters file.
        # The parameters are loaded from there by the code in the simulation
        # file
        env = os.environ.copy()
        env["SEASONAL_PARAMS_FILE"] = str(params_file)

        # Run the ODE Solver
        subprocess.run(
            [
                solver_command,
                "-s", str(simulation_file),
                "-q",
                "-ng",
                "-e", str(output_file),
            ],
            check=True,
            env=env,
        )

        # Load the JSON output by the ODE solver
        points = load_simulated_json(output_file)

        # Convert the points to monthly bins
        return monthly_average(points)


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
        forcing_peak = random_month_between(season_start, season_end)

    return {
        "GROWTH": "2.0",
        "DECAY": "1.5",
        "OOS_DECAY": "3.0",
        "SEASON_START": str(season_start),
        "SEASON_END": str(season_end),
        "SHARPNESS": str(round(random.uniform(2.0, 8.0), 3)),
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
        progress = (i + 1) / iterations
        bar = int(40 * progress)
        sys.stdout.write(f"\r[{'#' * bar}{'.' * (40 - bar)}] {i+1}/{iterations}")
        sys.stdout.flush()

        # Generate a random parameter set
        params = make_random_params(search_space)

        try:
            # Run the simulation and score the match
            simulated = run_solver(simulation_file, params, solver_command)
            score = weighted_score(observed, simulated)

            params["TIMESTAMP"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            params["OBSERVED"] = Path(observed_csv).name
            params["SCORE"] = str(score)

            append_params_to_csv(params, parameters_csv)

        except Exception as e:
            print(f"Trial {i + 1}: failed: {e}")
            continue


def append_params_to_csv(params: dict, csv_path: str):
    """
    Append the fitted parameters to a CSV file, one row per run
    
    :params dict: Set of simulation run parameters
    :params csv_path: CSV file to write to
    """
    columns = [
        "TIMESTAMP",
        "OBSERVED",
        "GROWTH",
        "DECAY",
        "OOS_DECAY",
        "SEASON_START",
        "SEASON_END",
        "SHARPNESS",
        "FORCING_PEAK",
        "SCORE",
        "WRAPS_YEAR",
    ]

    file_exists = os.path.exists(csv_path)

    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)

        # Write header if file doesn't exist
        if not file_exists:
            writer.writerow(columns)

        # Extract values in the correct order
        row = [params.get(col, "") for col in columns]
        writer.writerow(row)


def main():
    """
    Main entry point for the seasonal presence parameter fitter
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--observed", required=True, help="CSV file containing month,value columns")
    parser.add_argument("-s", "--simulation", required=True, help="Simulation JSON file for ODE Solver")
    parser.add_argument("-i", "--iterations", type=int, default=200, help="Number of parameter sets to test per run")
    parser.add_argument("-r", "--runs", type=int, default=1, help="Number of parameter fitting runs")
    parser.add_argument("-sc", "--solver-command", required=True, help="ODE Solver command")
    parser.add_argument("-c", "--csv", required=True, help="CSV file containing the accumulated data from multiple runs")
    parser.add_argument("--active-threshold", default="0.05", help="Observed value threshold used to infer active months")
    parser.add_argument("--season-padding", default="1.0", help="Padding around inferred season start/end, in months")
    parser.add_argument("--peak-padding", default="1.5", help="Padding around observed peak month, in months")
    args = parser.parse_args()

    observed = load_observed_csv(args.observed)
    search_space = infer_search_space(observed, D(str(args.active_threshold)), D(str(args.season_padding)), D(str(args.peak_padding)))

    print(format_search_space(search_space))

    fit(args.observed,
        args.csv,
        observed,
        Path(args.simulation),
        args.iterations,
        args.solver_command,
        search_space)


if __name__ == "__main__":
    main()
