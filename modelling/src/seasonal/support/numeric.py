from decimal import Decimal, InvalidOperation
from typing import Any, Optional
import random
import sys


def to_decimal(value: Any, name: str = None, error_type: type[Exception] = InvalidOperation) -> Decimal:
    """
    Convert one raw parameter value to ``Decimal``

    :param value: Raw value to convert, usually a number or numeric string from JSON
    :param name: Parameter name used in error messages
    :param error_type: Exception class to raise on failure
    :return: Converted ``Decimal`` value
    """
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        prefix = f"Parameter {name!r}" if name else "Value"
        message = f"{prefix} cannot be converted to Decimal: {value!r}"
        raise error_type(message) from exc


def D(value: Any) -> Decimal:
    """
    Safely convert a value to a Decimal.

    :param value: Value to convert
    :return: Decimal conversion of that value
    """
    return to_decimal(value)


def format_decimal(value: Any, places: int = 3) -> str:
    """
    Format a Decimal to 3 decimal places and return a string representation

    :param value: Value to format
    :param places: Number of decimal places
    :return: Value formatted as a string
    """
    value = D(value).quantize(Decimal("1." + "0" * places))
    return str(value.normalize())


def random_decimal(low: Any, high: Any, places: int = 3) -> Decimal:
    """
    Return a random Decimal between low and high.

    :param low: Minimum value
    :param high: Maximum value
    :param places: Number of decimal places
    :return: Random Decimal meeting the specified criteria
    """
    value = random.uniform(float(low), float(high))
    return D(round(value, places))


def show_progress(step_number: int, total_steps: int) -> None:
    """
    Display a status bar

    :param step_number: Current step number
    :param total_steps: Total number of steps to completion
    """
    progress = (step_number + 1) / total_steps
    bar = int(40 * progress)
    sys.stdout.write(f"\r[{'#' * bar}{'.' * (40 - bar)}] {step_number + 1}/{total_steps}")
    sys.stdout.flush()


def decimal_to_float(value: Decimal) -> float:
    """
    Convert a ``Decimal`` to a JSON-friendly float

    :param value: Decimal value to convert
    :return: Float representation of ``value``
    """
    return float(value)


def safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    """
    Return a ratio while avoiding division by zero

    :param numerator: Value to divide
    :param denominator: Value to divide by
    :return: ``numerator / denominator`` when possible, otherwise ``Decimal("0")``
    """
    if denominator == 0:
        return D("0")
    return numerator / denominator


def round_float(value: Optional[float], digits: int = 6) -> Optional[float]:
    """
    Round a floating point value to the specified number of digits, handling None inputs

    :param value: Value to round
    :param digits: Number of digits to round to
    :return: Rounded value or None
    """
    if value is None:
        return None
    return round(float(value), digits)


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    """
    Clip a floating point number to a range
    
    :param value: Value to clip
    :param minimum: Minimum of range
    :param maximum: Maximum of range
    """
    return max(minimum, min(maximum, value))
