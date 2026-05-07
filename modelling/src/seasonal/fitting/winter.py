from datetime import datetime
from pathlib import Path

from seasonal.support.utils import D, random_decimal, show_progress
from seasonal.support.calendar import circular_month_distance, month_range_around, random_month_in_range
from seasonal.support.scoring import mse
from seasonal.support.solver import run_solver
from seasonal.support.io import append_params_to_csv


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


def fit(observed_csv,
        parameters_csv,
        observed,
        simulation_file,
        iterations,
        solver_command,
        search_space,
        discard_months):
    """
    Parameter fitting loop
    
    :param observed: Observed behaviour being matched
    :param simulation_file: Path to the ODE Solver simulation file
    :param iterations: Number of iterations in the fit
    :param solver_command: Command used to run the ODE Solver
    :param search_space: Inferred search space
    :param discard_months: Number of months in the solution to discard
    """

    for i in range(iterations):
        show_progress(i, iterations)
        params = make_random_params(search_space)

        try:
            simulated = run_solver(simulation_file, params, solver_command, discard_months)
            score = weighted_score(observed, simulated)

            params["TIMESTAMP"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            params["OBSERVED"] = Path(observed_csv).name
            params["SCORE"] = str(score)

            append_params_to_csv(params, PARAMETER_COLUMNS, parameters_csv)

        except Exception as e:
            print(f"Trial {i + 1}: failed: {e}")
            continue
