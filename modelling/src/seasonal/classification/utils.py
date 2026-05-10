from decimal import Decimal
from typing import Any, Mapping
from seasonal.support.utils import D, to_decimal


def normalise_parameters(
        parameters: Mapping[str, Any],
        required: list[str],
        error_type: type[Exception]) -> dict[str, Decimal]:
    """
    Validate and normalise required resident-model parameters

    :param parameters: Raw parameter mapping read from a fitted parameter JSON file or equivalent source
    :return: Dictionary containing each required parameter converted to ``Decimal``
    :raises ResidentClassificationError: If any required parameter is missing or cannot be converted
    """
    missing = [name for name in required if name not in parameters]
    if missing:
        raise error_type(
            f"Missing required resident parameters: {', '.join(missing)}"
        )
    return {name: to_decimal(parameters[name], name, error_type) for name in required}


def validate_month(name: str, value: Decimal, warnings: list[str]) -> None:
    """
    Append a warning if a month-valued parameter lies outside the expected 1..12 range

    :param name: Name of the parameter being checked
    :param value: Month-like value to validate
    :param warnings: Mutable list that receives warning messages
    """
    if not (D("1") <= value <= D("12.999")):
        warnings.append(f"{name} lies outside the expected 1..12 month range.")
