from decimal import Decimal
from typing import Any
import random
import sys


def D(value: Any) -> Decimal:
    """
    Safely convert a value to a Decimal.

    :param value: Value to convert
    :return: Decimal conversion of that value
    """
    return Decimal(str(value))


def format_decimal(value: Any, places: int=3) -> str:
    """
    Format a Decimal to 3 decimal places and return a string representation

    :param value: Value to format
    :param places: Number of decimal places
    :return: Value formatted as a string
    """
    value = D(value).quantize(Decimal("1." + "0" * places))
    return str(value.normalize())


def random_decimal(low: Any, high: Any, places: int=3) -> Decimal:
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