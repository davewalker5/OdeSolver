"""
This contains the resident detectability model code extracted from the simulation file and is provided
for reference.
"""

import os
import json
from decimal import Decimal
from typing import Callable, TypeVar

T = TypeVar("T")
D = Decimal

# Useful constants
TWO_PI         = D("6.283185307179586476925286766559")
PI             = TWO_PI / D("2")
TWELVE         = D("12")
TWO            = D("2")
ONE            = D("1")
ZERO           = D("0")

def get_parameter(name: str, cast: Callable[[str], T] = Decimal) -> T:
    if not hasattr(get_parameter, "values"):
        file_path = os.environ["SEASONAL_PARAMS_FILE"]
        with open(file_path, mode="rt", encoding="utf-8") as json_f:
            get_parameter.values = json.load(json_f)

    if name not in get_parameter.values:
        return None

    return cast(get_parameter.values[name])


def pre_hook(options):
    # Get the initial value for Y
    value = get_parameter("INITIAL_Y")
    options["initial_value"] = value

    # Get the species - if it's specified, use it to set the chart title. Note
    # that this won't change the title in the UI for the first simulation pass
    # but will be shown in normalised results and exported charts
    species = get_parameter("SPECIES", str)
    if species:
        options["chart_title"] = f"Resident Detectability ({species})"


# Decimal sine via Taylor series
def d_sin(x: Decimal) -> Decimal:
    """Decimal sine using Taylor expansion."""
    x = x % TWO_PI
    if x > PI:
        x -= TWO_PI

    term = x
    result = x
    n = 1

    while True:
        term *= -x * x / D((2 * n) * (2 * n + 1))
        result += term

        if abs(term) < D("1e-20"):
            break

        n += 1

    return result


def d_cos(x: Decimal) -> Decimal:
    """Decimal cosine derived from sine."""
    return d_sin(x + PI / TWO)


def month_from_t(t: Decimal) -> Decimal:
    """
    Convert solver time into a repeating month number in the range 1..12.

    The solver typically runs from t = 0, so adding ONE makes t = 0 correspond
    to January / month 1 rather than month 0.
    """
    month = t + ONE
    return ((month - ONE) % TWELVE) + ONE


def annual_bump(t: Decimal, peak: Decimal, width: Decimal) -> Decimal:
    """
    Smooth annual bump centred on peak month.

    Returns a value in the range 0..1.

    width controls concentration:
      lower width = broader bump
      higher width = narrower bump

    Decimal does not reliably support fractional powers using the ** operator.
    Because width may be fractional, calculate profile ** width as:

        exp(width * ln(profile))

    with explicit handling for profile == 0.
    """
    angle = TWO_PI * (t - peak) / TWELVE
    profile = (ONE + d_cos(angle)) / TWO

    # Guard against tiny rounding artefacts from the Taylor-series trig.
    if profile <= ZERO:
        return ZERO
    if profile >= ONE:
        return ONE

    return (width * profile.ln()).exp()


def resident_target(t: Decimal) -> Decimal:
    """
    Resident seasonal detectability target.

    This is not a presence/absence model. It assumes the species is present all
    year, with detectability varying around a persistent get_parameter("BASELINE").
    """
    winter = annual_bump(t, get_parameter("WINTER_PEAK"), get_parameter("WINTER_WIDTH"))
    autumn = annual_bump(t, get_parameter("AUTUMN_PEAK"), get_parameter("AUTUMN_WIDTH"))
    summer = annual_bump(t, get_parameter("SUMMER_LOW"), get_parameter("SUMMER_WIDTH"))

    target = get_parameter("BASELINE") + get_parameter("WINTER_WEIGHT") * winter + get_parameter("AUTUMN_WEIGHT") * autumn - get_parameter("SUMMER_DIP") * summer

    # Keep the target non-negative in case parameters are pushed too far.
    if target < ZERO:
        return ZERO

    return target


def f(t: Decimal, y: Decimal) -> Decimal:
    """
    Resident detectability ODE.

    y relaxes towards a seasonal target rather than being created and destroyed
    by a seasonal growth/decay window.
    """
    t_mod = month_from_t(t)
    target = resident_target(t_mod)

    if target > y:
        rate = get_parameter("GROWTH_RATE")
    else:
        rate = get_parameter("DECAY_RATE")

    return rate * (target - y)