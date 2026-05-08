import random
from datetime import datetime
from pathlib import Path

from seasonal.support.utils import D, random_decimal, show_progress
from seasonal.support.calendar import circular_month_distance, month_range_around, random_month_in_range
from seasonal.support.solver import run_solver
from seasonal.support.io import append_params_to_csv


PARAMETER_COLUMNS = [
    "TIMESTAMP",
    "OBSERVED",
    "SCORE",
    "INITIAL_Y",
    "GROWTH_RATE",
    "DECAY_RATE",
    "SUMMER_DECAY_BOOST",
    "PRE_SUMMER_DECAY_REDUCTION",
    "PRE_SUMMER_DECAY_END",
    "PRE_SUMMER_DECAY_SHARPNESS",
    "SPRING_CARRYOVER_WEIGHT",
    "SPRING_CARRYOVER_END",
    "SPRING_CARRYOVER_SHARPNESS",
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
    "SUMMER_ONSET",
    "SUMMER_GATE_SHARPNESS",
    "SUMMER_DECAY_ONSET",
    "SUMMER_DECAY_GATE_SHARPNESS",
    "SUMMER_WIDTH",
    "SUMMER_RISE_WIDTH",
    "SUMMER_FALL_WIDTH",
    "SCALE",
    "YEAR_END_WEIGHT",
    "YEAR_END_PEAK",
    "YEAR_END_WIDTH",
    "YEAR_END_RISE_WIDTH",
    "YEAR_END_FALL_WIDTH",
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


def early_autumn_rise_penalty(
    observed,
    simulated,
    autumn_onset,
    weight=D("1.5"),
):
    """
    Penalise simulated late-year recovery that starts before the observed
    autumn onset.

    This is deliberately one-sided: it penalises being too high too early,
    but does not punish a cautious/delayed autumn rise.
    """
    if autumn_onset is None:
        return D("0")

    total = D("0")
    count = D("0")

    for month in range(7, 12):
        if D(month) >= D(autumn_onset):
            continue

        if month not in observed or month not in simulated:
            continue

        excess = D(simulated[month]) - D(observed[month])

        if excess > 0:
            total += excess ** 2
            count += D("1")

    if count == 0:
        return D("0")

    return D(weight) * total / count


def late_year_slope_penalty(
    observed,
    simulated,
    months=(8, 9, 10, 11),
    weight=D("2.0"),
):
    """
    Penalise simulated month-to-month rises that are steeper than observed
    during the late-year recovery period.
    """
    total = D("0")
    count = D("0")

    for m1, m2 in zip(months, months[1:]):
        if m1 not in observed or m2 not in observed:
            continue
        if m1 not in simulated or m2 not in simulated:
            continue

        obs_rise = D(observed[m2]) - D(observed[m1])
        sim_rise = D(simulated[m2]) - D(simulated[m1])

        excess_rise = sim_rise - obs_rise

        if excess_rise > 0:
            total += excess_rise ** 2
            count += D("1")

    if count == 0:
        return D("0")

    return D(weight) * total / count


def premature_late_year_peak_penalty(
    observed,
    simulated,
    months=(9, 10, 11, 12),
    weight=D("4.0"),
):
    """
    Penalise simulations where the late-year recovery peaks before the observed
    late-year peak.

    Useful for residents where the model lifts November too strongly instead
    of keeping the main recovery into December.
    """
    obs_late_peak = max(months, key=lambda m: observed.get(m, D("0")))
    sim_late_peak = max(months, key=lambda m: simulated.get(m, D("0")))

    if sim_late_peak < obs_late_peak:
        return D(weight) * D(obs_late_peak - sim_late_peak) ** 2

    return D("0")


def pre_december_recovery_penalty(
    observed,
    simulated,
    months=(9, 10, 11),
    weight=D("3.0"),
):
    """
    Penalise the model for rising too high before December.

    This helps species where the observed curve remains low/flat through
    autumn, then recovers sharply at year end.
    """
    total = D("0")
    count = D("0")

    for month in months:
        if month not in observed or month not in simulated:
            continue

        excess = D(simulated[month]) - D(observed[month])

        if excess > 0:
            total += excess ** 2
            count += D("1")

    if count == 0:
        return D("0")

    return D(weight) * total / count


def november_overfit_penalty(
    observed,
    simulated,
    weight=D("4.0"),
):
    if 11 not in observed or 11 not in simulated:
        return D("0")

    excess = D(simulated[11]) - D(observed[11])

    if excess <= 0:
        return D("0")

    return D(weight) * excess ** 2


def autumn_shelf_penalty(
    observed,
    simulated,
    months=(8, 9, 10),
    weight=D("6.0"),
):
    """
    Penalise the model for creating a broad autumn shelf before the true
    year-end recovery.
    """
    total = D("0")
    count = D("0")

    for month in months:
        if month not in observed or month not in simulated:
            continue

        excess = D(simulated[month]) - D(observed[month])

        if excess > 0:
            total += excess ** 2
            count += D("1")

    if count == 0:
        return D("0")

    return D(weight) * total / count


def weighted_score(
    observed,
    simulated,
    initial_y_weight=D("10.0"),
    initial_month=1,
    underestimation_weight=D("2.5"),
    min_simulated_floor=None,
    floor_weight=D("5.0"),
    autumn_onset=None,
    early_autumn_weight=D("1.5"),
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

    early_autumn_error = early_autumn_rise_penalty(
        observed,
        simulated,
        autumn_onset,
        early_autumn_weight,
    )

    late_year_slope_error = late_year_slope_penalty(
        observed,
        simulated,
        weight=D("2.0"),
    )

    late_peak_error = premature_late_year_peak_penalty(
        observed,
        simulated,
        weight=D("4.0"),
    )

    pre_december_error = pre_december_recovery_penalty(
        observed,
        simulated,
        weight=D("3.0"),
    )

    november_error = november_overfit_penalty(observed, simulated)

    autumn_shelf_error = autumn_shelf_penalty(
        observed,
        simulated,
        weight=D("6.0"),
    )

    return (
        error
        + D("0.20") * peak_error
        + D("0.20") * low_error
        + D(initial_y_weight) * initial_error
        + early_autumn_error
        + late_year_slope_error
        + late_peak_error
        + pre_december_error
        + november_error
        + autumn_shelf_error
    )


def infer_autumn_onset_from_observed(observed, summer_low_month):
    """
    Estimate when the observed late-year rise begins.

    Looks after the summer low and finds the first month where the observed
    value has recovered meaningfully from the summer low towards the late-year
    high.
    """
    summer_low_month = int(summer_low_month)

    candidate_months = [m for m in range(summer_low_month, 13)]
    if not candidate_months:
        return D("10")

    summer_low_value = observed.get(summer_low_month, min(observed.values()))

    late_year_months = [10, 11, 12]
    late_year_peak_value = max(observed.get(m, D("0")) for m in late_year_months)

    recovery = late_year_peak_value - summer_low_value

    if recovery <= D("0.05"):
        return D("11")

    threshold = summer_low_value + recovery * D("0.35")

    for month in candidate_months:
        if observed.get(month, D("0")) >= threshold:
            return D(month)

    return D("11")


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
    observed_autumn_onset = infer_autumn_onset_from_observed(observed, summer_low_centre)

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

    # Data-informed guard for the optional spring carry-over term.
    #
    # Blackbird-like residents keep a high proportion of their spring
    # detectability into June/July; blue-tit-like residents are already in a
    # steep decline by June.  In the latter case, a large positive carry-over
    # can make June artificially high.  This caps the optional carry-over
    # according to the observed spring -> June retention, while still allowing
    # blackbird-like curves to use the full range.
    spring_reference = max(
        observed.get(3, D("0")),
        observed.get(4, D("0")),
        observed.get(5, D("0")),
        D("0.0001"),
    )
    june_retention_ratio = observed.get(6, D("0")) / spring_reference

    if june_retention_ratio < D("0.50"):
        spring_carryover_weight_range = (D("0.00"), D("0.10"))
    elif june_retention_ratio < D("0.70"):
        spring_carryover_weight_range = (D("0.00"), D("0.22"))
    else:
        spring_carryover_weight_range = (D("0.00"), D("0.45"))

    return {
        "winter_peak_centre": winter_peak_centre,
        "winter_peak_range": month_range_around(winter_peak_centre, peak_padding),
        "autumn_peak_centre": autumn_peak_centre,
        "autumn_peak_range": month_range_around(autumn_peak_centre, D("1.5")),
        # Soft autumn gate: normally allow the late-year component to start
        # emerging sometime after the summer low and before the autumn/winter
        # peak. Keep this deliberately broad so it remains a fitted property,
        # not a hard ecological rule."observed_autumn_onset": observed_autumn_onset,
        "autumn_onset_range": (
            max(D("8.25"), summer_low_centre + D("1.25")),
            D("11.50"),
        ),
        "summer_low_centre": summer_low_centre,
        "summer_low_range": month_range_around(summer_low_centre, low_padding),
        # Summer onset controls when the summer dip is allowed to start
        # materially affecting the curve. This is deliberately inferred from
        # the observed low rather than hard-coded, so species with earlier
        # dips can still fit normally.
        "summer_onset_range": (
            max(D("3.50"), summer_low_centre - D("3.00")),
            max(D("5.00"), summer_low_centre - D("0.50")),
        ),
        "baseline_centre": baseline_centre,
        "baseline_floor": baseline_floor,
        "baseline_margin_low": baseline_margin_low,
        "baseline_margin_high": baseline_margin_high,
        "near_zero_baseline": near_zero_baseline,
        "initial_y_centre": initial_y_centre,
        "initial_y_range": (initial_y_low, initial_y_high),
        "scale_range": (scale_low, scale_high),
        "year_end_peak_range": month_range_around(D("12"), D("0.75")),
        # For blackbird-like residents, allow the fitted solution to retain
        # winter/spring detectability until late spring / early summer before
        # the sharp summer collapse begins.  The reduction itself can still fit
        # to zero for species such as blue tit.
        # Allow retention to last through June for blackbird-like curves.
        # Species that do not need this can still fit PRE_SUMMER_DECAY_REDUCTION
        # close to zero.
        "pre_summer_decay_end_range": (D("6.25"), D("7.75")),
        # Positive carry-over support for species whose spring/early-summer
        # detectability stays high until just before the summer trough.
        # This should be able to cover May-July for blackbird while still
        # switching off sharply enough to permit the August low.
        "spring_carryover_end_range": (D("6.50"), D("7.65")),
        "spring_carryover_weight_range": spring_carryover_weight_range,
        "june_retention_ratio": june_retention_ratio,
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
    summer_onset = random_decimal(*search_space["summer_onset_range"], 2)
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
    # The pre-low side of the summer dip often needs to be much sharper than
    # the old range allowed. Blackbird-like curves should stay high through
    # spring/early summer, then collapse quickly into the summer trough.
    summer_rise_width = random_decimal(D("0.35"), D("80.00"), 3)
    summer_fall_width = random_decimal(D("0.35"), D("20.00"), 3)

    # Keep the old single-width parameters as harmless compatibility values.
    # The asymmetric model uses the explicit *_RISE_WIDTH and *_FALL_WIDTH
    # values; older model files will simply ignore those extra keys.
    winter_width = (winter_rise_width + winter_fall_width) / D("2")
    autumn_width = (autumn_rise_width + autumn_fall_width) / D("2")
    summer_width = (summer_rise_width + summer_fall_width) / D("2")

    year_end_peak = random_decimal(D("12.00"), D("12.30"), 3)
    year_end_rise_width = random_decimal(D("80.00"), D("240.00"), 3)
    year_end_fall_width = random_decimal(D("4.00"), D("16.00"), 3)
    year_end_width = (year_end_rise_width + year_end_fall_width) / D("2")

    return {
        "INITIAL_Y": str(random_decimal(initial_y_low, initial_y_high, 3)),
        # Wider rates let the solution track a January/December high without
        # being dragged into an artificial February maximum by relaxation lag.
        "GROWTH_RATE": str(random_decimal(D("0.25"), D("4.00"), 3)),
        # Base decay may now be very slow; SUMMER_DECAY_BOOST can provide the
        # sharp summer collapse where the observed data need it.  The range is
        # deliberately backwards-compatible because it still includes the old
        # 0.50..6.00 behaviour.
        "DECAY_RATE": str(random_decimal(D("0.05"), D("6.00"), 3)),
        "SUMMER_DECAY_BOOST": str(random_decimal(D("0.00"), D("8.00"), 3)),
        "PRE_SUMMER_DECAY_REDUCTION": str(random_decimal(D("0.00"), D("0.95"), 3)),
        "PRE_SUMMER_DECAY_END": str(random_decimal(*search_space["pre_summer_decay_end_range"], 2)),
        "PRE_SUMMER_DECAY_SHARPNESS": str(random_decimal(D("3.00"), D("16.00"), 3)),
        # Positive spring/early-summer support.  This is the key additional
        # degree of freedom for blackbird-like curves: May-July can be held up
        # without globally slowing decay or weakening the true summer dip.
        "SPRING_CARRYOVER_WEIGHT": str(random_decimal(*search_space["spring_carryover_weight_range"], 3)),
        "SPRING_CARRYOVER_END": str(random_decimal(*search_space["spring_carryover_end_range"], 2)),
        "SPRING_CARRYOVER_SHARPNESS": str(random_decimal(D("6.00"), D("28.00"), 3)),
        "BASELINE": str(random_decimal(baseline_low, baseline_high, 3)),
        # Bias towards high-baseline residents: mostly present all year, with
        # seasonal modulation rather than seasonal near-absence.
        "WINTER_WEIGHT": str(random_decimal(D("0.00"), D("0.75"), 3)),
        "AUTUMN_WEIGHT": str(random_decimal(D("0.00"), D("0.05"), 3)),
        "WINTER_PEAK": str(winter_peak),
        "AUTUMN_PEAK": str(autumn_peak),
        "AUTUMN_ONSET": str(autumn_onset),
        "AUTUMN_GATE_SHARPNESS": str(random_decimal(D("2.00"), D("12.00"), 3)),
        "WINTER_WIDTH": str(winter_width.quantize(D("0.001"))),
        "WINTER_RISE_WIDTH": str(winter_rise_width),
        "WINTER_FALL_WIDTH": str(winter_fall_width),
        "AUTUMN_WIDTH": str(autumn_width.quantize(D("0.001"))),
        "AUTUMN_RISE_WIDTH": str(autumn_rise_width),
        "AUTUMN_FALL_WIDTH": str(autumn_fall_width),
        "SUMMER_DIP": str(random_decimal(D("0.00"), D("0.25"), 3)),
        "SUMMER_LOW": str(summer_low),
        "SUMMER_ONSET": str(summer_onset),
        "SUMMER_GATE_SHARPNESS": str(random_decimal(D("0.80"), D("8.00"), 3)),
        # Separate timing for the *rate acceleration* into the dip.  This is
        # deliberately later and sharper than SUMMER_ONSET so May/June can stay
        # high while July/August still collapse.
        "SUMMER_DECAY_ONSET": str(random_decimal(D("6.60"), D("7.60"), 2)),
        "SUMMER_DECAY_GATE_SHARPNESS": str(random_decimal(D("6.00"), D("24.00"), 3)),
        "SUMMER_WIDTH": str(summer_width.quantize(D("0.001"))),
        "SUMMER_RISE_WIDTH": str(summer_rise_width),
        "SUMMER_FALL_WIDTH": str(summer_fall_width),
        "SCALE": str(random_decimal(scale_low, scale_high, 3)),
        "YEAR_END_WEIGHT": str(random_decimal(D("0.00"), D("0.35"), 3)),
        "YEAR_END_PEAK": str(year_end_peak),
        "YEAR_END_WIDTH": str(year_end_width.quantize(D("0.001"))),
        "YEAR_END_RISE_WIDTH": str(year_end_rise_width),
        "YEAR_END_FALL_WIDTH": str(year_end_fall_width),
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
                search_space.get("observed_autumn_onset"),
            )

            params["TIMESTAMP"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            params["OBSERVED"] = Path(observed_csv).name
            params["SCORE"] = str(score)

            append_params_to_csv(params, PARAMETER_COLUMNS, parameters_csv)

        except Exception as e:
            print(f"Trial {i + 1}: failed: {e}")
            continue
