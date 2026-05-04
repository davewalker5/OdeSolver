#!/usr/bin/env python3
"""
Parameter fitter for the winter visitor model.

This is intended for species such as Redwing or Fieldfare, where presence is
concentrated across the calendar boundary: late autumn / winter / early spring.

The fitter:

- Loads observed monthly data from a CSV file containing month,value columns
- Normalises observed values to 0..1
- Infers useful peak centres from the observed curve
- Generates random winter-model parameter sets
- Runs the ODE Solver headlessly with SEASONAL_PARAMS_FILE
- Scores the simulated curve against the observed curve
- Repeats for N iterations and M runs
- Writes the best parameters to JSON and appends best-per-run rows to CSV
"""

import argparse
import csv
import json
import os
import random
import subprocess
import tempfile
from datetime import datetime
from decimal import Decimal
from pathlib import Path


PARAMETER_COLUMNS = [
    "TIMESTAMP",
    "OBSERVED",
    "SCORE",
    "INITIAL_Y",
    "GROWTH_RATE",
    "DECAY_RATE",
    "BASELINE",
    "WINTER_WEIGHT",
    "AUTUMN_WEIGHT",
    "WINTER_PEAK",
    "AUTUMN_PEAK",
    "WINTER_WIDTH",
    "AUTUMN_WIDTH",
    "SUMMER_DIP",
    "SUMMER_LOW",
    "SUMMER_WIDTH",
]


def D(value):
    """
    Safely convert a value to a Decimal

    :param value: Value to convert
    :return: The Decimal conversion of that value
    """
    return Decimal(str(value))


def random_decimal(low, high, places=3):
    """
    Return a random Decimal between low and high
    
    :param low: Minimum value
    :param hight: Maximum value
    :param places: Number of decimal places
    :return: Random decimal meeting the specified criteria
    """
    value = random.uniform(float(low), float(high))
    return D(round(value, places))


def wrap_month(value):
    """
    Wrap a month-like value into the range 1..12
    
    :param value: Unwrapped month number
    :return: wrapped month number
    """
    value = D(value)

    while value < D("1"):
        value += D("12")

    while value > D("12"):
        value -= D("12")

    return value


def circular_month_distance(a, b):
    """
    Shortest distance between two month-like values on a circular year
    
    :param a: First month
    :param b: Second month
    :return: Shortest distance between the two months, on a "clock-face" type circle
    """
    a = D(a)
    b = D(b)
    diff = abs(a - b)
    return min(diff, D("12") - diff)


def month_range_around(centre, padding):
    """
    Create a possibly wrapped month range around a centre month
    
    :param centre: Month to wrap around
    :param padding: Number of months either side of the central month
    :return: Wrapped month range
    """
    return wrap_month(D(centre) - D(padding)), wrap_month(D(centre) + D(padding))


def random_month_in_range(low, high):
    """
    Select a random Decimal month from a possibly wrapped range.

    :param low: Initial month number
    :param high: Final month number
    :return: Wrapped random month number in the specified range
    """
    low = D(low)
    high = D(high)

    if low <= high:
        return D(round(random.uniform(float(low), float(high)), 2))

    # Wrapped range: choose from low..12 or 1..high, weighted by length.
    late_length = D("12") - low
    early_length = high - D("1")
    total_length = late_length + early_length

    if total_length <= 0:
        return wrap_month(low)

    if D(str(random.random())) < late_length / total_length:
        return D(round(random.uniform(float(low), 12.0), 2))

    return D(round(random.uniform(1.0, float(high)), 2))


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
    rows = {}

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = int(row["month"])
            value = D(row["value"])
            rows[month] = value

    max_value = max(rows.values())

    if max_value == 0:
        return {m: D("0") for m in rows}

    return {month: value / max_value for month, value in rows.items()}


def load_simulated_json(path):
    """
    Load the JSON format simulation output

    :param path: Path to the simulation output file
    :return: A list of dictionaries, each representing a point (t, y)
    """
    with open(path) as f:
        data = json.load(f)

    points = []

    for p in data:
        y_key = "y_normalised" if "y_normalised" in p else "y"
        points.append({"t": D(p["t"]), "y": D(p[y_key])})

    return points


def monthly_average(points, discard_months=D("0")):
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
    discard_months = D(discard_months)

    for p in points:
        t = p["t"]

        if t < discard_months:
            continue

        adjusted_t = t - discard_months
        month = int(adjusted_t % D("12")) + 1

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
    months = sorted(set(observed) & set(simulated))

    if not months:
        raise ValueError("No overlapping months between observed and simulated data")

    return sum((observed[m] - simulated[m]) ** 2 for m in months) / D(len(months))


def active_months(data, threshold=D("0.05")):
    """
    Return months whose value is above the active threshold

    :param data: Dataset to examine
    :return: List of month numbers
    """
    return sorted(m for m, v in data.items() if v > threshold)


def weighted_score(observed, simulated, threshold=D("0.05")):
    """
    Score the fit for a winter visitor.

    This combines:
    - MSE curve error
    - peak month mismatch
    - active-month mismatch

    It avoids assuming a simple non-wrapped start/end window, because winter
    visitor presence naturally crosses the calendar boundary.
    """
    curve_error = mse(observed, simulated)

    observed_peak = max(observed, key=observed.get)
    simulated_peak = max(simulated, key=simulated.get)
    peak_error = circular_month_distance(observed_peak, simulated_peak) / D("12")

    obs_active = set(active_months(observed, threshold))
    sim_active = set(active_months(simulated, threshold))

    if obs_active or sim_active:
        active_mismatch = D(len(obs_active ^ sim_active)) / D("12")
    else:
        active_mismatch = D("1")

    return curve_error + D("0.25") * peak_error + D("0.25") * active_mismatch


def infer_winter_search_space(observed, peak_padding=D("1.5")):
    """
    Infer biologically plausible parameter ranges for a winter visitor model
    from observed monthly data.

    The observed data is used to identify:

    - The main winter peak
    - The late-autumn / early-winter return
    - The summer low point

    These inferred features are then expanded into circular month ranges
    so the random search explores plausible values without being allowed
    to wander into ecologically unlikely parts of the year.

    This is especially important for winter visitors, where the active
    season crosses the calendar boundary.

    WINTER_PEAK is centred on the observed annual peak.
    AUTUMN_PEAK is centred on the strongest late-year month, usually Nov/Dec.
    INITIAL_Y is centred on the January observed value because the model starts
    at the beginning of the year.

    :param observed: Observed data
    :return: Definition of the search space for random parameter generation
    """
    winter_peak_centre = D(max(observed, key=observed.get))

    late_year_candidates = {m: observed.get(m, D("0")) for m in [10, 11, 12]}
    autumn_peak_centre = D(max(late_year_candidates, key=late_year_candidates.get))

    # If there is no late-year signal, keep the autumn bump possible but centred
    # near December as a harmless default.
    if late_year_candidates[int(autumn_peak_centre)] == 0:
        autumn_peak_centre = D("12")

    return {
        "winter_peak_centre": winter_peak_centre,
        "winter_peak_range": month_range_around(winter_peak_centre, peak_padding),
        "autumn_peak_centre": autumn_peak_centre,
        "autumn_peak_range": month_range_around(autumn_peak_centre, D("1.0")),
        "initial_y_centre": observed.get(1, D("0")),
    }


def format_search_space(search_space):
    """
    Format inferred search space for console output
    
    :param search_space: Search space for random parameter generation
    """
    def fmt_range(r):
        return f"{r[0]}..{r[1]}"

    return "\n".join([
        "Inferred winter visitor search space",
        "------------------------------------",
        f"Winter peak centre: {search_space['winter_peak_centre']}",
        f"Winter peak range:  {fmt_range(search_space['winter_peak_range'])}",
        f"Autumn peak centre: {search_space['autumn_peak_centre']}",
        f"Autumn peak range:  {fmt_range(search_space['autumn_peak_range'])}",
        f"Initial Y centre:   {search_space['initial_y_centre']}",
    ])


def make_random_params(search_space):
    """
    Generate a random set of parameters for the model.

    The random ranges are inferred from the observed data, allowing the fitter to
    handle both summer visitors and winter visitors. For winter visitors, season
    start/end can wrap across the end of the year, e.g. October..March.

    :param search_space: Search space inferred from observed data
    :return: Dictionary of parameter values
    """
    winter_peak = random_month_in_range(*search_space["winter_peak_range"])
    autumn_peak = random_month_in_range(*search_space["autumn_peak_range"])

    initial_centre = D(search_space["initial_y_centre"])
    initial_low = max(D("0"), initial_centre - D("0.35"))
    initial_high = min(D("1.25"), initial_centre + D("0.35"))

    return {
        "INITIAL_Y": str(random_decimal(initial_low, initial_high, 3)),
        "GROWTH_RATE": str(random_decimal(D("0.20"), D("2.00"), 3)),
        "DECAY_RATE": str(random_decimal(D("0.40"), D("3.50"), 3)),
        "BASELINE": "0.0",
        "WINTER_WEIGHT": str(random_decimal(D("0.70"), D("1.50"), 3)),
        "AUTUMN_WEIGHT": str(random_decimal(D("0.00"), D("0.80"), 3)),
        "WINTER_PEAK": str(winter_peak),
        "AUTUMN_PEAK": str(autumn_peak),
        "WINTER_WIDTH": str(random_decimal(D("0.80"), D("4.00"), 3)),
        "AUTUMN_WIDTH": str(random_decimal(D("1.00"), D("6.00"), 3)),
        "SUMMER_DIP": str(random_decimal(D("0.00"), D("0.40"), 3)),
        "SUMMER_LOW": str(random_decimal(D("5.50"), D("8.00"), 2)),
        "SUMMER_WIDTH": str(random_decimal(D("1.00"), D("5.00"), 3)),
    }


def run_solver(simulation_file, params, solver_command, discard_months):
    """Run ODE Solver with a temporary parameter file."""
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        params_file = tmp / "winter_params.json"
        output_file = tmp / "output.json"

        params_file.write_text(json.dumps(params, indent=2))

        env = os.environ.copy()
        env["SEASONAL_PARAMS_FILE"] = str(params_file)

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

        points = load_simulated_json(output_file)
        return monthly_average(points, discard_months=discard_months)


def fit(observed, simulation_file, iterations, solver_command, search_space, discard_months):
    """
    Parameter fitting loop
    
    :param observed: Observed behaviour being matched
    :param simulation_file: Path to the ODE Solver simulation file
    :param iterations: Number of iterations in the fit
    :param solver_command: Command used to run the ODE Solver
    :param search_space: 
    :param discard_months: Number of months in the solution to discard
    :return: A dictionary of parameters yielding the best fit
    """
    best = None

    for i in range(iterations):
        params = make_random_params(search_space)

        try:
            simulated = run_solver(simulation_file, params, solver_command, discard_months)
            score = weighted_score(observed, simulated)

        except Exception as e:
            print(f"Trial {i + 1}: failed: {e}")
            continue

        if best is None or score < best["score"]:
            best = {
                "score": score,
                "params": params,
                "simulated": simulated,
            }

            print()
            print(f"New best at trial {i + 1}")
            print(f"Score: {score}")
            print(json.dumps(params, indent=2))

    return best


def append_params_to_csv(params, csv_path):
    """
    Append the fitted parameters to a CSV file, one row per run
    
    :params dict: Set of simulation run parameters
    :params csv_path: CSV file to write to
    """
    file_exists = os.path.exists(csv_path)

    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(PARAMETER_COLUMNS)

        writer.writerow([params.get(col, "") for col in PARAMETER_COLUMNS])


def main():
    """
    Main entry point for the winter visitor parameter fitter
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--observed", required=True, help="CSV file containing month,value columns")
    parser.add_argument("-s", "--simulation", required=True, help="Simulation JSON file for ODE Solver")
    parser.add_argument("-i", "--iterations", type=int, default=200, help="Number of parameter sets to test per run")
    parser.add_argument("-r", "--runs", type=int, default=1, help="Number of parameter fitting runs")
    parser.add_argument("-sc", "--solver-command", required=True, help="ODE Solver command")
    parser.add_argument("-b", "--best-output", default="best_params.json", help="Where to write the best parameter file")
    parser.add_argument("-c", "--csv", required=True, help="CSV file to accumulate best parameters from multiple runs")
    parser.add_argument("--peak-padding", type=Decimal, default=Decimal("1.5"), help="Search padding around observed winter peak")
    parser.add_argument("--discard-months", type=Decimal, default=Decimal("0"), help="Ignore this many initial simulation months before binning output")

    args = parser.parse_args()

    observed = load_observed_csv(args.observed)
    search_space = infer_winter_search_space(observed, peak_padding=args.peak_padding)

    print(format_search_space(search_space))

    for r in range(args.runs):
        print()
        print(f"Starting winter visitor parameter fitting run {r + 1}\n")

        best = fit(
            observed=observed,
            simulation_file=Path(args.simulation),
            iterations=args.iterations,
            solver_command=args.solver_command,
            search_space=search_space,
            discard_months=args.discard_months,
        )

        if best is None:
            raise RuntimeError("No successful parameter set found")

        best["params"]["TIMESTAMP"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        best["params"]["OBSERVED"] = Path(args.observed).name
        best["params"]["SCORE"] = str(best["score"])

        Path(args.best_output).write_text(json.dumps(best["params"], indent=2) + "\n")
        append_params_to_csv(best["params"], args.csv)

        print()
        print("Best fit")
        print("--------")
        print(f"Score: {best['score']}")
        print(json.dumps(best["params"], indent=2))
        print()
        print(f"Wrote: {args.best_output}")


if __name__ == "__main__":
    main()
