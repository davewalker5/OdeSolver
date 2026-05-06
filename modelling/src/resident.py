import argparse
import random
import sys
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from fitting.utils import D, random_decimal, show_progress
from fitting.calendar import circular_month_distance, month_range_around, random_month_in_range
from fitting.solver import run_solver, export_simulation
from fitting.io import append_params_to_csv, load_and_normalise_observed_csv
from fitting.consensus import write_consensus_parameters
from fitting.synthesise import synthesise
from fitting.tabulate import print_args_table, print_dict_table


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
    "AUTUMN_ONSET",
    "AUTUMN_GATE_SHARPNESS",
    "WINTER_WIDTH",
    "WINTER_RISE_WIDTH",
    "WINTER_FALL_WIDTH",
    "AUTUMN_WIDTH",
    "AUTUMN_RISE_WIDTH",
    "AUTUMN_FALL_WIDTH",
    "SUMMER_DIP",
    "SUMMER_LOW",
    "SUMMER_WIDTH",
    "SUMMER_RISE_WIDTH",
    "SUMMER_FALL_WIDTH",
    "SCALE",
]


def asymmetric_width_pair(low, high, places=3, asymmetry_chance=0.85):
    """
    Return rise/fall width parameters for an asymmetric seasonal bump.

    Most trials are allowed to be asymmetric; some are deliberately near-
    symmetric so the fitter can still rediscover the old model shape where it
    is appropriate. Higher values mean a narrower/steeper side of the bump.
    """
    base = random_decimal(low, high, places)

    if random.random() > asymmetry_chance:
        jitter = random_decimal(D("0.85"), D("1.15"), places)
        rise = max(D(low), min(D(high), base * jitter))
        fall = max(D(low), min(D(high), base / jitter))
        return rise.quantize(D("0.001")), fall.quantize(D("0.001"))

    rise = random_decimal(low, high, places)
    fall = random_decimal(low, high, places)
    return rise, fall


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
    # For resident birds with a January maximum, the initial value is not a
    # throwaway transient: it is part of the annual cycle.  Give the fitter
    # enough room to start high rather than forcing the solution to climb
    # towards a February peak.
    initial_y_low = max(D("0.00"), initial_y_centre - D("0.25"))
    initial_y_high = min(D("2.00"), initial_y_centre + D("0.35"))

    scale_low = D("0.80")
    scale_high = D("1.80")

    return {
        "winter_peak_centre": winter_peak_centre,
        "winter_peak_range": month_range_around(winter_peak_centre, peak_padding),
        "autumn_peak_centre": autumn_peak_centre,
        "autumn_peak_range": month_range_around(autumn_peak_centre, D("1.5")),
        # Soft autumn gate: normally allow the late-year component to start
        # emerging sometime after the summer low and before the autumn/winter
        # peak. Keep this deliberately broad so it remains a fitted property,
        # not a hard ecological rule.
        "autumn_onset_range": (D("6.50"), D("11.25")),
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
    autumn_onset = random_decimal(*search_space["autumn_onset_range"], 2)

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

    # Broader search than v1.  Magpie / woodpigeon-like residents often need
    # a sharp post-winter fall but only weak overall modulation.
    winter_rise_width, winter_fall_width = asymmetric_width_pair(D("0.35"), D("20.00"), 3)
    autumn_rise_width, autumn_fall_width = asymmetric_width_pair(D("0.35"), D("14.00"), 3)
    summer_rise_width, summer_fall_width = asymmetric_width_pair(D("0.35"), D("14.00"), 3)

    # Keep the old single-width parameters as harmless compatibility values.
    # The asymmetric model uses the explicit *_RISE_WIDTH and *_FALL_WIDTH
    # values; older model files will simply ignore those extra keys.
    winter_width = (winter_rise_width + winter_fall_width) / D("2")
    autumn_width = (autumn_rise_width + autumn_fall_width) / D("2")
    summer_width = (summer_rise_width + summer_fall_width) / D("2")

    return {
        "INITIAL_Y": str(random_decimal(initial_y_low, initial_y_high, 3)),
        # Wider rates let the solution track a January/December high without
        # being dragged into an artificial February maximum by relaxation lag.
        "GROWTH_RATE": str(random_decimal(D("0.25"), D("4.00"), 3)),
        "DECAY_RATE": str(random_decimal(D("0.50"), D("6.00"), 3)),
        "BASELINE": str(random_decimal(baseline_low, baseline_high, 3)),
        # Bias towards high-baseline residents: mostly present all year, with
        # seasonal modulation rather than seasonal near-absence.
        "WINTER_WEIGHT": str(random_decimal(D("0.00"), D("0.75"), 3)),
        "AUTUMN_WEIGHT": str(random_decimal(D("0.00"), D("0.45"), 3)),
        "WINTER_PEAK": str(winter_peak),
        "AUTUMN_PEAK": str(autumn_peak),
        "AUTUMN_ONSET": str(autumn_onset),
        "AUTUMN_GATE_SHARPNESS": str(random_decimal(D("0.50"), D("8.00"), 3)),
        "WINTER_WIDTH": str(winter_width.quantize(D("0.001"))),
        "WINTER_RISE_WIDTH": str(winter_rise_width),
        "WINTER_FALL_WIDTH": str(winter_fall_width),
        "AUTUMN_WIDTH": str(autumn_width.quantize(D("0.001"))),
        "AUTUMN_RISE_WIDTH": str(autumn_rise_width),
        "AUTUMN_FALL_WIDTH": str(autumn_fall_width),
        "SUMMER_DIP": str(random_decimal(D("0.00"), D("0.25"), 3)),
        "SUMMER_LOW": str(summer_low),
        "SUMMER_WIDTH": str(summer_width.quantize(D("0.001"))),
        "SUMMER_RISE_WIDTH": str(summer_rise_width),
        "SUMMER_FALL_WIDTH": str(summer_fall_width),
        "SCALE": str(random_decimal(scale_low, scale_high, 3)),
    }


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
    :param underestimation_weight:
    :param min_simulated_floor: 
    :param floor_weight: 
    """

    for i in range(iterations):
        show_progress(i, iterations)
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

            append_params_to_csv(params, PARAMETER_COLUMNS, parameters_csv)

        except Exception as e:
            print(f"Trial {i + 1}: failed: {e}")
            continue


def main():
    """
    Main entry point for the resident detectability parameter fitter.
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-sp", "--species", required="True", help="Species name")
    parser.add_argument("-o", "--observed", required=True, help="CSV file containing month,value columns")
    parser.add_argument("-s", "--simulation", required=True, help="Simulation JSON file for ODE Solver")
    parser.add_argument("-i", "--iterations", type=int, default=200, help="Number of parameter sets to test per run")
    parser.add_argument("-sc", "--solver-command", required=True, help="ODE Solver command")
    parser.add_argument("-c", "--csv", required=True, help="CSV file to accumulate the parameters from each iteration")
    parser.add_argument("-cj", "--consensus-json", required=True, help="JSON file to write the consensus parameters to")
    parser.add_argument("-esi", "--export-simulated", required=True, help="CSV file containing the simulated output")
    parser.add_argument("-psi", "--plot-simulated", required=True, help="PNG file containing the simulated chart")
    parser.add_argument("-esy", "--export-synthesised", required=True, help="CSV file containing the synthesised output")
    parser.add_argument("-psy", "--plot-synthesised", required=True, help="PNG file containing the synthesised chart")
    parser.add_argument("-sm", "--scale-method", choices=["least_squares", "max", "sum"], default="least_squares", help="How to rescale the simulated shape onto the observed scale")
    parser.add_argument("-a", "--aggregation", choices=["mean", "max", "last"], default="mean", help="How to convert the solver's sub-monthly output into monthly values")
    parser.add_argument("-r", "--round", action="store_true", help="Round synthesised values to integer counts")
    parser.add_argument("-tp", "--top-percent", type=Decimal, default=Decimal("20"), help="Top percentage of rows to use in the consensus, sorted by SCORE")
    parser.add_argument("-pp", "--peak-padding", type=Decimal, default=Decimal("1.5"), help="Search padding around observed detectability peak")
    parser.add_argument("-lp", "--low-padding", type=Decimal, default=Decimal("1.5"), help="Search padding around observed low point")
    parser.add_argument("-d", "--discard-months", type=Decimal, default=Decimal("0"), help="Ignore this many initial simulation months before binning output")
    parser.add_argument("-iw", "--initial-y-weight", type=Decimal, default=Decimal("4.0"), help="Weight applied to the initial-condition mismatch penalty. Use 0 to disable. Default: 4.0")
    parser.add_argument("-im", "--initial-month", type=int, default=1, help="Month used as the initial-condition anchor. Default: 1 / January")
    parser.add_argument("-uw", "--underestimation-weight", type=Decimal, default=Decimal("2.5"), help="Penalty multiplier when simulated values fall below observed values. Default: 2.5")
    parser.add_argument("-mf", "--min-simulated-floor", type=Decimal, default=Decimal("0.60"), help="Optional floor for scaled simulated monthly values. Useful for high-baseline residents, e.g. 0.60")
    parser.add_argument("-fw", "--floor-weight", type=Decimal, default=Decimal("5.0"), help="Penalty multiplier for falling below --min-simulated-floor. Default: 5.0")
    args = parser.parse_args()
    print_args_table(args, "Resident Detectability Model Arguments")

    # Load the observed data and calculate the search space
    observed = load_and_normalise_observed_csv(args.observed)
    search_space = infer_resident_search_space(observed, args.peak_padding, args.low_padding)
    print_dict_table(search_space, "Inferred Search Space")

    # Generate the parameter fitting CSV
    print()
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

    # Write the consensus parameter set
    write_consensus_parameters(args.csv, args.consensus_json, args.species, PARAMETER_COLUMNS, args.top_percent)

    # Run the solution using the consensus parameters and export the simulated results CSV and chart
    export_simulation(args.solver_command, args.consensus_json, args.simulation, args.export_simulated, args.plot_simulated)

    # Generate the synthesised data
    synthesise(args.species, args.observed, args.export_simulated, args.export_synthesised, args.plot_synthesised, args.scale_method, args.aggregation, args.round)


if __name__ == "__main__":
    main()
