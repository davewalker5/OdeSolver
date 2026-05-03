"""
This contains the winter visitor model code extracted from the simulation file and is provided
for reference.
"""

import os
import json
from decimal import Decimal

D = Decimal

# Useful constants
TWO_PI = D("6.283185307179586476925286766559")
PI     = TWO_PI / D("2")
TWELVE = D("12")
TWO    = D("2")
ONE    = D("1")
ZERO   = D("0")

def get_parameter(name: str) -> Decimal:
    if not hasattr(get_parameter, "values"):
        file_path = os.environ["SEASONAL_PARAMS_FILE"]
        with open(file_path, mode="rt", encoding="utf-8") as json_f:
            get_parameter.values = json.load(json_f)

    return Decimal(get_parameter.values[name])


def pre_hook(options):
    value = get_parameter("INITIAL_Y")
    options["initial_value"] = value


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
    """
    angle = TWO_PI * (t - peak) / TWELVE
    profile = (ONE + d_cos(angle)) / TWO

    if profile <= ZERO:
        return ZERO
    if profile >= ONE:
        return ONE

    return profile ** get_parameter("SHARPNESS")


def winter_visitor_target(t: Decimal) -> Decimal:
    """
    Seasonal target for a winter visitor.

    High in winter, possibly rising again in late autumn / early winter,
    and close to zero through late spring and summer.
    """
    winter = annual_bump(t, get_parameter("WINTER_PEAK"), get_parameter("WINTER_WIDTH"))
    autumn = annual_bump(t, get_parameter("AUTUMN_PEAK"), get_parameter("AUTUMN_WIDTH"))
    summer = annual_bump(t, get_parameter("SUMMER_LOW"), get_parameter("SUMMER_WIDTH"))

    target = (
        get_parameter("BASELINE")
        + get_parameter("WINTER_WEIGHT") * winter
        + get_parameter("AUTUMN_WEIGHT") * autumn
        - get_parameter("SUMMER_DIP") * summer
    )

    if target < ZERO:
        return ZERO

    return target


def f(t: Decimal, y: Decimal) -> Decimal:
    """
    Winter visitor ODE.

    y relaxes towards a periodic winter target. This avoids the hard
    year-boundary problem seen when a single-year seasonal presence model
    starts from zero in January.
    """
    t_mod = month_from_t(t)
    target = winter_visitor_target(t_mod)

    if target > y:
        rate = get_parameter("GROWTH_RATE")
    else:
        rate = get_parameter("DECAY_RATE")

    return rate * (target - y)
