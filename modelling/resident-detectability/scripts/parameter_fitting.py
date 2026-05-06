"""
Parameter fitter for the resident detectability model.

This is intended for species such as Robin, Blackbird, Wren, etc. where the
species is assumed to be present year-round, but observable activity /
detectability varies seasonally.

The fitter:

- Loads observed monthly data from a CSV file containing month,value columns
- Normalises observed values to 0..1
- Infers useful peak/low centres from the observed curve
- Generates random resident-model parameter sets
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
import sys
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
    "SCALE",
]


def D(value):
    """
    Safely convert a value to a Decimal.

    :param value: Value to convert
    :return: Decimal conversion of that value
    """
    return Decimal(str(value))


def random_decimal(low, high, places=3):
    """
    Return a random Decimal between low and high.

    :param low: Minimum value
    :param high: Maximum value
    :param places: Number of decimal places
    :return: Random Decimal meeting the specified criteria
    """
    value = random.uniform(float(low), float(high))
    return D(round(value, places))


def wrap_month(value):
    """
    Wrap a month-like value into the range 1..12.

    :param value: Unwrapped month number
    :return: Wrapped month number
    """
    value = D(value)

    while value < D("1"):
        value += D("12")

    while value > D("12"):
        value -= D("12")

    return value


def circular_month_distance(a, b):
    """
    Shortest distance between two month-like values on a circular year.

    :param a: First month
    :param b: Second month
    :return: Shortest distance between the two months on a circular year
    """
    a = D(a)
    b = D(b)
    diff = abs(a - b)
    return min(diff, D("12") - diff)


def month_range_around(centre, padding):
    """
    Create a possibly wrapped month range around a centre month.

    :param centre: Centre month
    :param padding: Number of months either side of the centre
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
    Load the observed data and normalise it into the range 0..1.

    The CSV file is expected to contain:
    - month: month number, 1..12
    - value: observed presence/detectability/count value

    :param path: Path to observed CSV
    :return: Normalised observed data keyed by month
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
    Load JSON simulation output from the ODE Solver.

    :param path: Path to simulation output file
    :return: List of dictionaries, each containing t and y
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
    Convert solver output points into monthly bins.

    t = 0.0..0.999 -> month 1
    t = 1.0..1.999 -> month 2
    ...
    t = 11.0..11.999 -> month 12

    If discard_months is supplied, the initial portion of the simulation is
    ignored before binning. This can be useful if the simulation is run with
    a warm-up period.

    :param points: List of solution points
    :param discard_months: Number of initial simulation months to discard
    :return: Dictionary of monthly averaged values
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


def scale_simulated(simulated, scale):
    """
    Apply a fitted vertical scale to the simulated monthly values.

    The resident model often gets the seasonal shape broadly right but sits too
    low or too high overall. SCALE is a fitter-side correction that lets the
    random search compare curves at the right vertical level without changing
    the seasonal-shape parameters themselves.

    :param simulated: Simulated monthly values
    :param scale: Multiplicative scale factor
    :return: Scaled simulated monthly values
    """
    scale = D(scale)
    return {month: D(value) * scale for month, value in simulated.items()}


def curve_error(
    observed,
    simulated,
    underestimation_weight=D("2.5"),
    min_simulated_floor=None,
    floor_weight=D("5.0"),
):
    """
    Calculate weighted curve error between observed and simulated data.

    This replaces plain MSE for resident species where false collapses are more
    damaging than modest overestimates. Months where the simulation is below
    the observation can be penalised more strongly, and an optional floor can
    discourage unrealistically deep dips.

    :param observed: Observed monthly values
    :param simulated: Simulated monthly values
    :param underestimation_weight: Extra multiplier when simulated < observed
    :param min_simulated_floor: Optional minimum acceptable simulated value
    :param floor_weight: Penalty multiplier for falling below the floor
    :return: Mean weighted squared error
    """
    months = sorted(set(observed) & set(simulated))

    if not months:
        raise ValueError("No overlapping months between observed and simulated data")

    total = D("0")

    for month in months:
        diff = D(simulated[month]) - D(observed[month])
        weight = D(underestimation_weight) if diff < 0 else D("1.0")
        total += weight * (diff ** 2)

        if min_simulated_floor is not None and D(simulated[month]) < D(min_simulated_floor):
            floor_diff = D(min_simulated_floor) - D(simulated[month])
            total += D(floor_weight) * (floor_diff ** 2)

    return total / D(len(months))


def initial_condition_penalty(observed, simulated, initial_month=1):
    """
    Penalise mismatch between the first observed month and the corresponding
    simulated monthly value.

    This is useful for resident species where the initial state represents a
    real baseline detectability level rather than an arbitrary transient.

    :param observed: Observed monthly values
    :param simulated: Simulated monthly values
    :param initial_month: Month to anchor, normally 1 because t=0 is January
    :return: Squared initial-condition error
    """
    if initial_month not in observed or initial_month not in simulated:
        return D("0")

    return (observed[initial_month] - simulated[initial_month]) ** 2


def weighted_score(
    observed,
    simulated,
    initial_y_weight=D("10.0"),
    initial_month=1,
    underestimation_weight=D("2.5"),
    min_simulated_floor=None,
    floor_weight=D("5.0"),
):
    """
    Score the fit for a resident detectability model.

    This combines:
    - MSE curve error
    - annual peak timing mismatch
    - summer low timing mismatch
    - explicit initial-condition mismatch penalty

    Unlike the winter visitor fitter, this does not penalise simulated presence
    in zero/near-zero months. The resident model assumes the species is present
    year-round and only detectability varies.

    The initial-condition penalty is deliberately separate from MSE. Without it,
    a low INITIAL_Y can be hidden by later growth/relaxation, especially when
    the rest of the seasonal curve is a good match.
    """
    error = curve_error(
        observed,
        simulated,
        underestimation_weight=underestimation_weight,
        min_simulated_floor=min_simulated_floor,
        floor_weight=floor_weight,
    )
    initial_error = initial_condition_penalty(
        observed,
        simulated,
        initial_month=initial_month,
    )

    observed_peak = max(observed, key=observed.get)
    simulated_peak = max(simulated, key=simulated.get)
    peak_error = circular_month_distance(observed_peak, simulated_peak) / D("12")

    observed_low = min(observed, key=observed.get)
    simulated_low = min(simulated, key=simulated.get)
    low_error = circular_month_distance(observed_low, simulated_low) / D("12")

    return (
        error
        + D("0.20") * peak_error
        + D("0.20") * low_error
        + D(initial_y_weight) * initial_error
    )


def infer_resident_search_space(observed, peak_padding=D("1.5"), low_padding=D("1.5")):
    """
    Infer biologically plausible parameter ranges for a resident detectability
    model from observed monthly data.
    """
    winter_peak_centre = D(max(observed, key=observed.get))

    late_year_candidates = {m: observed.get(m, D("0")) for m in [10, 11, 12]}
    autumn_peak_centre = D(max(late_year_candidates, key=late_year_candidates.get))

    if late_year_candidates[int(autumn_peak_centre)] == 0:
        autumn_peak_centre = D("12")

    summer_low_centre = D(min(observed, key=observed.get))

    values = list(observed.values())
    max_value = max(values)
    min_value = min(values)

    zero_months = sum(1 for v in values if v == 0)

    # Detect resident-like species whose record pattern has a strong seasonal
    # spike but little or no off-season detectability.
    near_zero_baseline = (
        min_value == 0
        or zero_months >= 3
        or min_value <= max_value * D("0.05")
    )

    if near_zero_baseline:
        baseline_centre = D("0.01")
        baseline_floor = D("0.00")
        baseline_margin_low = D("0.01")
        baseline_margin_high = D("0.08")
    else:
        baseline_centre = min_value
        baseline_floor = D("0.05")
        baseline_margin_low = D("0.25")
        baseline_margin_high = D("0.35")

    initial_y_centre = observed.get(1, baseline_centre)
    initial_y_low = max(D("0.00"), initial_y_centre - D("0.60"))
    initial_y_high = min(D("2.00"), initial_y_centre + D("0.90"))

    scale_low = D("0.80")
    scale_high = D("1.80")

    return {
        "winter_peak_centre": winter_peak_centre,
        "winter_peak_range": month_range_around(winter_peak_centre, peak_padding),
        "autumn_peak_centre": autumn_peak_centre,
        "autumn_peak_range": month_range_around(autumn_peak_centre, D("1.5")),
        "summer_low_centre": summer_low_centre,
        "summer_low_range": month_range_around(summer_low_centre, low_padding),
        "baseline_centre": baseline_centre,
        "baseline_floor": baseline_floor,
        "baseline_margin_low": baseline_margin_low,
        "baseline_margin_high": baseline_margin_high,
        "near_zero_baseline": near_zero_baseline,
        "initial_y_centre": initial_y_centre,
        "initial_y_range": (initial_y_low, initial_y_high),
        "scale_range": (scale_low, scale_high),
    }


def format_search_space(search_space):
    """
    Format inferred search space for console output.

    :param search_space: Search space for random parameter generation
    :return: Formatted string
    """
    def fmt_range(r):
        return f"{r[0]}..{r[1]}"

    return "\n".join([
        "\nInferred Resident Detectability Search Space",
        "--------------------------------------------",
        f"Winter peak centre: {search_space['winter_peak_centre']}",
        f"Winter peak range:  {fmt_range(search_space['winter_peak_range'])}",
        f"Autumn peak centre: {search_space['autumn_peak_centre']}",
        f"Autumn peak range:  {fmt_range(search_space['autumn_peak_range'])}",
        f"Summer low centre:  {search_space['summer_low_centre']}",
        f"Summer low range:   {fmt_range(search_space['summer_low_range'])}",
        f"Baseline centre:    {search_space['baseline_centre']}",
        f"Initial Y centre:   {search_space['initial_y_centre']}",
        f"Initial Y range:    {fmt_range(search_space['initial_y_range'])}",
        f"Scale range:        {fmt_range(search_space['scale_range'])}",
        "\n"
    ])


def make_random_params(search_space):
    """
    Generate a random set of parameters for the resident detectability model.

    Supports both ordinary resident species with a positive baseline and
    'resident-like' species with near-zero off-season detectability, such as
    spring-spiking persistent annuals.
    """
    winter_peak = random_month_in_range(*search_space["winter_peak_range"])
    autumn_peak = random_month_in_range(*search_space["autumn_peak_range"])
    summer_low = random_month_in_range(*search_space["summer_low_range"])

    baseline_centre = D(search_space["baseline_centre"])

    baseline_floor = D(search_space.get("baseline_floor", "0.05"))
    baseline_margin_low = D(search_space.get("baseline_margin_low", "0.25"))
    baseline_margin_high = D(search_space.get("baseline_margin_high", "0.35"))

    baseline_low = max(baseline_floor, baseline_centre - baseline_margin_low)
    baseline_high = min(D("0.90"), baseline_centre + baseline_margin_high)

    # Safety: if the inferred centre is very low, allow a small but usable range
    if baseline_high <= baseline_low:
        baseline_high = baseline_low + D("0.10")

    initial_y_low, initial_y_high = search_space["initial_y_range"]
    scale_low, scale_high = search_space["scale_range"]

    return {
        "INITIAL_Y": str(random_decimal(initial_y_low, initial_y_high, 3)),
        "GROWTH_RATE": str(random_decimal(D("0.15"), D("1.50"), 3)),
        "DECAY_RATE": str(random_decimal(D("0.30"), D("2.50"), 3)),
        "BASELINE": str(random_decimal(baseline_low, baseline_high, 3)),
        "WINTER_WEIGHT": str(random_decimal(D("0.00"), D("1.20"), 3)),
        "AUTUMN_WEIGHT": str(random_decimal(D("0.00"), D("0.35"), 3)),
        "WINTER_PEAK": str(winter_peak),
        "AUTUMN_PEAK": str(autumn_peak),
        "WINTER_WIDTH": str(random_decimal(D("0.80"), D("5.00"), 3)),
        "AUTUMN_WIDTH": str(random_decimal(D("1.00"), D("6.00"), 3)),
        "SUMMER_DIP": str(random_decimal(D("0.00"), D("0.35"), 3)),
        "SUMMER_LOW": str(summer_low),
        "SUMMER_WIDTH": str(random_decimal(D("1.00"), D("5.00"), 3)),
        "SCALE": str(random_decimal(scale_low, scale_high, 3)),
    }


def run_solver(simulation_file, params, solver_command, discard_months):
    """
    Run ODE Solver with a temporary parameter file.

    :param simulation_file: Path to the simulation JSON
    :param params: Parameter dictionary
    :param solver_command: ODE Solver command
    :param discard_months: Initial months to discard when binning
    :return: Monthly simulated values
    """
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        params_file = tmp / "resident_params.json"
        output_file = tmp / "output.json"

        # SCALE is used by the fitter after simulation.  Do not pass it to the
        # ODE solver unless the model explicitly supports it.
        solver_params = {k: v for k, v in params.items() if k != "SCALE"}
        params_file.write_text(json.dumps(solver_params, indent=2))

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


def fit(observed_csv,
        parameters_csv,
        observed,
        simulation_file,
        iterations,
        solver_command,
        search_space,
        discard_months,
        initial_y_weight,
        initial_month,
        underestimation_weight,
        min_simulated_floor,
        floor_weight):
    """
    Parameter fitting loop.

    :param observed_csv: Path to the observed data file
    :param parameters_csv: Path to the output parameters CSV file
    :param observed: Observed behaviour being matched
    :param simulation_file: Path to ODE Solver simulation file
    :param iterations: Number of iterations in the fit
    :param solver_command: Command used to run ODE Solver
    :param search_space: Inferred search space
    :param discard_months: Initial simulation months to discard
    :param initial_y_weight: Weight applied to initial-condition mismatch
    :param initial_month: Month used for the initial-condition anchor
    :param min_simulated_floor: 
    :param floor_weight: 
    """

    for i in range(iterations):
        progress = (i + 1) / iterations
        bar = int(40 * progress)
        sys.stdout.write(f"\r[{'#' * bar}{'.' * (40 - bar)}] {i+1}/{iterations}")
        sys.stdout.flush()

        params = make_random_params(search_space)

        try:
            raw_simulated = run_solver(simulation_file, params, solver_command, discard_months)
            simulated = scale_simulated(raw_simulated, params.get("SCALE", "1.0"))
            score = weighted_score(
                observed,
                simulated,
                initial_y_weight,
                initial_month,
                underestimation_weight,
                min_simulated_floor,
                floor_weight,
            )

            params["TIMESTAMP"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            params["OBSERVED"] = Path(observed_csv).name
            params["SCORE"] = str(score)

            append_params_to_csv(params, parameters_csv)

        except Exception as e:
            print(f"Trial {i + 1}: failed: {e}")
            continue


def append_params_to_csv(params, csv_path):
    """
    Append fitted parameters to a CSV file, one row per run.

    :param params: Fitted simulation parameters
    :param csv_path: CSV file to write to
    """
    file_exists = os.path.exists(csv_path)

    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(PARAMETER_COLUMNS)

        writer.writerow([params.get(col, "") for col in PARAMETER_COLUMNS])


def main():
    """
    Main entry point for the resident detectability parameter fitter.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-o", "--observed", required=True, help="CSV file containing month,value columns")
    parser.add_argument("-s", "--simulation", required=True, help="Simulation JSON file for ODE Solver")
    parser.add_argument("-i", "--iterations", type=int, default=200, help="Number of parameter sets to test per run")
    parser.add_argument("-r", "--runs", type=int, default=1, help="Number of parameter fitting runs")
    parser.add_argument("-sc", "--solver-command", required=True, help="ODE Solver command")
    parser.add_argument("-c", "--csv", required=True, help="CSV file to accumulate best parameters from multiple runs")
    parser.add_argument("-pp", "--peak-padding", type=Decimal, default=Decimal("1.5"), help="Search padding around observed detectability peak")
    parser.add_argument("-lp", "--low-padding", type=Decimal, default=Decimal("1.5"), help="Search padding around observed low point")
    parser.add_argument("-d", "--discard-months", type=Decimal, default=Decimal("0"), help="Ignore this many initial simulation months before binning output")
    parser.add_argument("-iw", "--initial-y-weight", type=Decimal, default=Decimal("0.5"), help="Weight applied to the initial-condition mismatch penalty. Use 0 to disable. Default: 10.0")
    parser.add_argument("-im", "--initial-month", type=int, default=1, help="Month used as the initial-condition anchor. Default: 1 / January")
    parser.add_argument("-uw", "--underestimation-weight", type=Decimal, default=Decimal("2.5"), help="Penalty multiplier when simulated values fall below observed values. Default: 2.5")
    parser.add_argument("-mf", "--min-simulated-floor", type=Decimal, default=Decimal("0.4"), help="Optional floor for scaled simulated monthly values. Useful for resident species with no true seasonal absence, e.g. 0.40")
    parser.add_argument("-fw", "--floor-weight", type=Decimal, default=Decimal("5.0"), help="Penalty multiplier for falling below --min-simulated-floor. Default: 5.0")

    args = parser.parse_args()

    observed = load_observed_csv(args.observed)
    search_space = infer_resident_search_space(observed, args.peak_padding, args.low_padding)

    print(format_search_space(search_space))

    fit(args.observed,
        args.csv,
        observed,
        Path(args.simulation),
        args.iterations,
        args.solver_command,
        search_space,
        args.discard_months,
        args.initial_y_weight,
        args.initial_month,
        args.underestimation_weight,
        args.min_simulated_floor,
        args.floor_weight,
    )


if __name__ == "__main__":
    main()
