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


def get_parameter_or(name: str, default: Decimal) -> Decimal:
    """
    Read a Decimal parameter, returning a default when it is absent.

    This keeps the asymmetric model backward-compatible with older fitted
    parameter JSON files that only contain WINTER_WIDTH / AUTUMN_WIDTH /
    SUMMER_WIDTH.
    """
    value = get_parameter(name)

    if value is None:
        return default

    return value


def signed_month_distance(t: Decimal, peak: Decimal) -> Decimal:
    """
    Signed shortest month distance from peak to t, in the range -6..+6.

    Negative values are before the peak in the annual cycle; positive values
    are after the peak. This lets each bump have a different pre-peak and
    post-peak width while still wrapping cleanly around December/January.
    """
    delta = (t - peak + D("6")) % TWELVE - D("6")
    return delta


def asymmetric_annual_bump(
    t: Decimal,
    peak: Decimal,
    rise_width: Decimal,
    fall_width: Decimal,
) -> Decimal:
    """
    Smooth annual bump with independent pre-peak and post-peak concentration.

    The underlying shape is still the same cosine-derived 0..1 profile used by
    annual_bump(), but the exponent is chosen according to which side of the
    peak the current month lies on:

    - rise_width: months before the peak
    - fall_width: months after the peak

    Higher width values create a narrower/steeper side. Lower values create a
    broader/slower side.
    """
    angle = TWO_PI * (t - peak) / TWELVE
    profile = (ONE + d_cos(angle)) / TWO

    if profile <= ZERO:
        return ZERO
    if profile >= ONE:
        return ONE

    delta = signed_month_distance(t, peak)
    width = rise_width if delta <= ZERO else fall_width

    return (width * profile.ln()).exp()



def autumn_onset_gate(t: Decimal, onset: Decimal, sharpness: Decimal) -> Decimal:
    """
    Smooth gate for the autumn component.

    Returns a value in the range 0..1. The gate is close to 0 before the
    fitted onset month and approaches 1 after it. This is deliberately a soft
    transition rather than a hard month constraint.

    Higher sharpness values make the transition faster; lower values make the
    transition more gradual.
    """
    if onset is None or sharpness is None:
        return ONE

    sharpness = D(sharpness)

    if sharpness <= ZERO:
        return ONE

    x = sharpness * (D(t) - D(onset))

    # Avoid unnecessary Decimal.exp work at extremes.
    if x > D("40"):
        return ONE
    if x < D("-40"):
        return ZERO

    return ONE / (ONE + (-x).exp())

def resident_target(t: Decimal) -> Decimal:
    """
    Resident seasonal detectability target.

    This is not a presence/absence model. It assumes the species is present all
    year, with detectability varying around a persistent BASELINE.

    The seasonal bumps are asymmetric. Older single-width parameter files still
    work because *_RISE_WIDTH and *_FALL_WIDTH fall back to the corresponding
    *_WIDTH value.

    The autumn bump can also be multiplied by a smooth onset gate. This lets
    the fitter delay the late-year rise without imposing a hard calendar-month
    cut-off. Older parameter files remain compatible: if AUTUMN_ONSET or
    AUTUMN_GATE_SHARPNESS is absent, the gate returns 1 and the model behaves
    like the asymmetric v2 model.
    """
    winter_width = get_parameter("WINTER_WIDTH")
    autumn_width = get_parameter("AUTUMN_WIDTH")
    summer_width = get_parameter("SUMMER_WIDTH")

    winter = asymmetric_annual_bump(
        t,
        get_parameter("WINTER_PEAK"),
        get_parameter_or("WINTER_RISE_WIDTH", winter_width),
        get_parameter_or("WINTER_FALL_WIDTH", winter_width),
    )
    autumn = asymmetric_annual_bump(
        t,
        get_parameter("AUTUMN_PEAK"),
        get_parameter_or("AUTUMN_RISE_WIDTH", autumn_width),
        get_parameter_or("AUTUMN_FALL_WIDTH", autumn_width),
    )
    autumn *= autumn_onset_gate(
        t,
        get_parameter("AUTUMN_ONSET"),
        get_parameter("AUTUMN_GATE_SHARPNESS"),
    )
    summer = asymmetric_annual_bump(
        t,
        get_parameter("SUMMER_LOW"),
        get_parameter_or("SUMMER_RISE_WIDTH", summer_width),
        get_parameter_or("SUMMER_FALL_WIDTH", summer_width),
    )

    year_end = asymmetric_annual_bump(
        t,
        get_parameter("YEAR_END_PEAK"),
        get_parameter_or("YEAR_END_RISE_WIDTH", get_parameter("YEAR_END_WIDTH")),
        get_parameter_or("YEAR_END_FALL_WIDTH", get_parameter("YEAR_END_WIDTH")),
    )

    target = (
        get_parameter("BASELINE")
        + get_parameter("WINTER_WEIGHT") * winter
        + get_parameter("AUTUMN_WEIGHT") * autumn
        + get_parameter("YEAR_END_WEIGHT") * year_end
        - get_parameter("SUMMER_DIP") * summer
    )

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