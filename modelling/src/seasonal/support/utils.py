from decimal import Decimal, InvalidOperation
from typing import Any, Optional
import random
import sys
import math


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


def format_search_space(search_space: dict) -> str:
    """
    Format the inferred search space for console output

    :param search_space: Search space for random parameter generation
    :return: Formatted string
    """

    rows = [
        "\n",
        "Inferred Search Space",
        "---------------------",
    ] + [f"{k} : {v}" for k, v in search_space.items()] + ["\n"]

    return "\n".join(rows)


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


def coerce_json_value(value: Any) -> Any:
    """
    Convert values into JSON-friendly scalar representations

    :param value: Value that may include ``Decimal`` or other non-JSON-native types
    :return: JSON-friendly value suitable for inclusion in the classification output
    """
    if isinstance(value, Decimal):
        return float(value)
    try:
        Decimal(str(value))
        return float(value)
    except Exception:
        return value


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


def safe_float(value: Any) -> Optional[float]:
    """
    Return the floating point conversion of the specified value or None if conversion fails

    :param value: Value to convert
    :return: float conversion or None
    """
    if value is None:
        return None

    try:
        result = float(value)
    except (TypeError, ValueError):
        return None

    if math.isnan(result) or math.isinf(result):
        return None

    return result
