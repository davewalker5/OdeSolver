"""
This contains the resident detectability model code extracted from the simulation file and is provided
for reference.
"""

from decimal import Decimal

D = Decimal

# ------------------------------------------------------------
# Main dynamic parameter
# ------------------------------------------------------------

RESPONSE_RATE = D("0.8")     # How quickly y tracks the seasonal target

# ------------------------------------------------------------
# Resident detectability profile parameters
# ------------------------------------------------------------

BASELINE       = D("0.45")   # Year-round minimum detectability
WINTER_WEIGHT  = D("0.65")   # Winter / early-spring detectability contribution
AUTUMN_WEIGHT  = D("0.30")   # Autumn / early-winter recovery contribution
SUMMER_DIP     = D("0.35")   # Mid-year reduction in detectability

WINTER_PEAK    = D("2.5")    # Peak of winter / early-spring detectability
AUTUMN_PEAK    = D("12.5")   # Peak of autumn / early-winter detectability
SUMMER_LOW     = D("7.5")    # Centre of the summer dip

WINTER_WIDTH   = D("1.8")    # Lower = broader; higher = narrower
AUTUMN_WIDTH   = D("3.8")
SUMMER_WIDTH   = D("2.5")

GROWTH_RATE = D("0.45")      # Growth rate
DECAY_RATE  = D("1.0")       # Faster decay rate

# Useful constants
TWO_PI         = D("6.283185307179586476925286766559")
PI             = TWO_PI / D("2")
TWELVE         = D("12")
TWO            = D("2")
ONE            = D("1")
ZERO           = D("0")

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
    year, with detectability varying around a persistent baseline.
    """
    winter = annual_bump(t, WINTER_PEAK, WINTER_WIDTH)
    autumn = annual_bump(t, AUTUMN_PEAK, AUTUMN_WIDTH)
    summer = annual_bump(t, SUMMER_LOW, SUMMER_WIDTH)

    target = BASELINE + WINTER_WEIGHT * winter + AUTUMN_WEIGHT * autumn - SUMMER_DIP * summer

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
        rate = GROWTH_RATE
    else:
        rate = DECAY_RATE

    return rate * (target - y)