"""
This contains the seasonal presence model code extracted from the simulation file and is provided
for reference.
"""

import os
import json
from decimal import Decimal

from typing import Callable, TypeVar

T = TypeVar("T")
D = Decimal

# Useful constants
TWO_PI = D("6.283185307179586476925286766559")
PI     = TWO_PI / D("2")
TWELVE = D("12")
TWO    = D("2")
ONE    = D("1")
ZERO   = D("0")


def get_parameter(name: str, cast: Callable[[str], T] = Decimal) -> T:
    if not hasattr(get_parameter, "values"):
        file_path = os.environ["SEASONAL_PARAMS_FILE"]
        with open(file_path, mode="rt", encoding="utf-8") as json_f:
            get_parameter.values = json.load(json_f)

    if name not in get_parameter.values:
        return None

    return cast(get_parameter.values[name])


def pre_hook(options):
    # Get the species - if it's specified, use it to set the chart title. Note
    # that this won't change the title in the UI for the first simulation pass
    # but will be shown in normalised results and exported charts
    species = get_parameter("SPECIES", str)
    if species:
        options["chart_title"] = f"Seasonal Presence ({species})"


# Decimal exponential (uses built-in Decimal exp)
def d_exp(x: Decimal) -> Decimal:
    return x.exp()


# Decimal sine via Taylor series
def d_sin(x: Decimal) -> Decimal:
    # Normalize x to [-pi, pi]
    x = x % TWO_PI
    if x > PI:
        x -= TWO_PI

    term = x
    result = x
    n = 1

    while True:
        term *= -x * x / D((2*n)*(2*n+1))
        result += term
        if abs(term) < D("1e-20"):
            break
        n += 1

    return result


def d_cos(x: Decimal) -> Decimal:
    return d_sin(x + PI / TWO)


def seasonal_window(t: Decimal) -> Decimal:
    rise = ONE / (ONE + d_exp(-get_parameter("SHARPNESS") * (t - get_parameter("SEASON_START"))))
    fall = ONE / (ONE + d_exp(get_parameter("SHARPNESS") * (t - get_parameter("SEASON_END"))))
    return rise * fall


def calculate_decay(w: Decimal) -> Decimal:
    return get_parameter("DECAY") + get_parameter("OOS_DECAY") * (ONE - w)


def f(t: Decimal, y: Decimal) -> Decimal:
    # t will run from e.g. 0 to 12 months in small steps, so it's offset
    # from the true month number by 1
    month = t + ONE

    # Wrap time onto a 1..12 month cycle rather than 0..11.
    # This keeps December as month 12, not month 0.
    t_mod = ((month - ONE) % TWELVE) + ONE

    # Seasonal window
    W = seasonal_window(t_mod)

    # Decay factor
    decay = calculate_decay(W)

    # Seasonal forcing (pure Decimal raised cosine).
    # This gives a smooth 0..1 annual forcing curve with its maximum at
    # FORCING_PEAK, avoiding a hard zero in the first months of the year.
    S = (ONE + d_cos(TWO_PI * (t_mod - get_parameter("FORCING_PEAK")) / TWELVE)) / TWO

    # ODE
    return get_parameter("GROWTH") * S * W - decay * y
