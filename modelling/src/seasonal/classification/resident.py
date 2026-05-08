from __future__ import annotations

import json
import math
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Optional

from seasonal.support.utils import D
from seasonal.support.calendar import MONTH_NAMES


REQUIRED_PARAMETERS = [
    "INITIAL_Y",
    "GROWTH_RATE",
    "DECAY_RATE",
    "SUMMER_DECAY_BOOST",
    "PRE_SUMMER_DECAY_REDUCTION",
    "PRE_SUMMER_DECAY_END",
    "PRE_SUMMER_DECAY_SHARPNESS",
    "SPRING_CARRYOVER_WEIGHT",
    "SPRING_CARRYOVER_END",
    "SPRING_CARRYOVER_SHARPNESS",
    "BASELINE",
    "WINTER_WEIGHT",
    "AUTUMN_WEIGHT",
    "WINTER_PEAK",
    "AUTUMN_PEAK",
    "AUTUMN_ONSET",
    "AUTUMN_GATE_SHARPNESS",
    "WINTER_WIDTH",
    "WINTER_RISE_WIDTH",
    "WINTER_FALL_WIDTH",
    "AUTUMN_WIDTH",
    "AUTUMN_RISE_WIDTH",
    "AUTUMN_FALL_WIDTH",
    "SUMMER_DIP",
    "SUMMER_LOW",
    "SUMMER_ONSET",
    "SUMMER_GATE_SHARPNESS",
    "SUMMER_DECAY_ONSET",
    "SUMMER_DECAY_GATE_SHARPNESS",
    "SUMMER_WIDTH",
    "SUMMER_RISE_WIDTH",
    "SUMMER_FALL_WIDTH",
    "SCALE",
    "YEAR_END_WEIGHT",
    "YEAR_END_PEAK",
    "YEAR_END_WIDTH",
    "YEAR_END_RISE_WIDTH",
    "YEAR_END_FALL_WIDTH",
]


@dataclass(frozen=True)
class ResidentClassificationOptions:
    """
    Thresholds used by the rule-based resident model classifier

    These defaults are deliberately plain and tuneable. They are not intended
    as ecological constants; they simply turn fitted parameters/curve features
    into consistent interpretation labels
    """

    high_baseline_min: Decimal = D("0.30")
    moderate_baseline_min: Decimal = D("0.12")

    strong_spring_carryover_min: Decimal = D("0.22")
    moderate_spring_carryover_min: Decimal = D("0.10")

    strong_summer_dip_min: Decimal = D("0.16")
    moderate_summer_dip_min: Decimal = D("0.08")

    strong_summer_decay_boost_min: Decimal = D("4.0")
    moderate_summer_decay_boost_min: Decimal = D("2.5")

    strong_pre_summer_retention_min: Decimal = D("0.45")
    moderate_pre_summer_retention_min: Decimal = D("0.25")

    meaningful_autumn_ratio_min: Decimal = D("0.12")
    weak_autumn_ratio_min: Decimal = D("0.04")

    meaningful_year_end_ratio_min: Decimal = D("0.30")

    high_score_max: Decimal = D("0.20")
    medium_score_max: Decimal = D("0.35")


class ResidentClassificationError(ValueError):
    """Raised when resident model parameters cannot be classified"""


def classify_resident_model_to_json(
    parameters: Mapping[str, Any],
    output_path: str | Path,
    species: Optional[str] = None,
    score: Optional[Any] = None,
    options: ResidentClassificationOptions | None = None,
    indent: int = 2,
) -> dict[str, Any]:
    """
    Classify fitted resident-model parameters and write the classification JSON file

    :param parameters: Mapping of fitted resident model parameter names to values. Must include all entries in ``REQUIRED_PARAMETERS`` and may also include metadata such as ``SPECIES`` or ``SCORE``
    :param output_path: Destination path for the generated classification JSON file. Parent directories are created if needed
    :param species: Optional species name to use in the output. If omitted, ``parameters["SPECIES"]`` is used when available
    :param score: Optional fit score to include in the output. If omitted, ``parameters["SCORE"]`` is used when available
    :param options: Optional threshold set controlling how numeric parameters are converted into categorical traits
    :param indent: JSON indentation level used when writing the output file
    :return: The same JSON-serialisable classification dictionary that is written to ``output_path``
    """

    classification = classify_resident_model(
        parameters,
        species=species,
        score=score,
        options=options,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wt", encoding="utf-8") as json_f:
        json.dump(classification, json_f, indent=indent, ensure_ascii=False)
        json_f.write("\n")

    return classification


def classify_resident_model(
    parameters: Mapping[str, Any],
    species: Optional[str] = None,
    score: Optional[Any] = None,
    options: ResidentClassificationOptions | None = None,
) -> dict[str, Any]:
    """
    Classify fitted resident detectability parameters into ecological traits

    :param parameters: Mapping of fitted resident model parameter names to values. Values are normalised to ``Decimal`` before classification
    :param species: Optional species name to use in the output. If omitted, ``parameters["SPECIES"]`` is used when available
    :param score: Optional fit score used to derive a broad confidence label. If omitted, ``parameters["SCORE"]`` is used when available
    :param options: Optional threshold set controlling baseline, carry-over, suppression, retention, and confidence labels
    :return: JSON-serialisable dictionary containing classification labels, derived metrics, parameter evidence, warnings, and a prose summary
    """

    options = options or ResidentClassificationOptions()
    p = _normalise_parameters(parameters)

    species_name = species or str(parameters.get("SPECIES", "Unknown species"))
    fit_score = score if score is not None else parameters.get("SCORE")

    warnings: list[str] = []
    for name in [
        "WINTER_PEAK",
        "AUTUMN_PEAK",
        "AUTUMN_ONSET",
        "SUMMER_LOW",
        "SUMMER_ONSET",
        "SUMMER_DECAY_ONSET",
        "YEAR_END_PEAK",
        "PRE_SUMMER_DECAY_END",
        "SPRING_CARRYOVER_END",
    ]:
        _validate_month(name, p[name], warnings)

    if p["BASELINE"] < 0:
        warnings.append(
            "Baseline is negative; expected persistent non-negative detectability."
        )
    if p["SUMMER_DIP"] < 0:
        warnings.append(
            "Summer dip is negative; expected a non-negative summer suppression term."
        )
    if p["WINTER_WEIGHT"] < 0 or p["AUTUMN_WEIGHT"] < 0 or p["YEAR_END_WEIGHT"] < 0:
        warnings.append(
            "One or more seasonal support weights are negative; expected non-negative support terms."
        )

    monthly_target = _monthly_target_values(p)
    peak_month = max(monthly_target, key=monthly_target.get)
    trough_month = min(monthly_target, key=monthly_target.get)
    peak_value = monthly_target[peak_month]
    trough_value = monthly_target[trough_month]
    mean_value = sum(monthly_target.values(), D("0")) / D("12")
    amplitude = peak_value - trough_value

    baseline_presence = _classify_baseline(p["BASELINE"], options)
    spring_carryover = _classify_spring_carryover(p["SPRING_CARRYOVER_WEIGHT"], options)
    summer_suppression = _classify_summer_suppression(p["SUMMER_DIP"], options)
    summer_decay = _classify_summer_decay(p["SUMMER_DECAY_BOOST"], options)
    pre_summer_retention = _classify_pre_summer_retention(
        p["PRE_SUMMER_DECAY_REDUCTION"], options
    )
    autumn_component = _classify_autumn_component(
        _safe_ratio(p["AUTUMN_WEIGHT"], p["WINTER_WEIGHT"]), options
    )
    year_end_component = _classify_year_end_component(
        _safe_ratio(p["YEAR_END_WEIGHT"], p["WINTER_WEIGHT"]), options
    )
    peak_timing = _classify_timing(D(peak_month))
    trough_timing = _classify_timing(D(trough_month))
    response_dynamics = _classify_response_dynamics(
        p["GROWTH_RATE"], p["DECAY_RATE"], p["SUMMER_DECAY_BOOST"]
    )

    primary_class = _primary_class(
        baseline_presence=baseline_presence,
        spring_carryover=spring_carryover,
        summer_suppression=summer_suppression,
        summer_decay=summer_decay,
        peak_timing=peak_timing,
        trough_timing=trough_timing,
    )

    traits = [
        "resident_detectability_pattern",
        f"{baseline_presence}_baseline_presence",
        f"{peak_timing}_detectability_peak",
        f"{trough_timing}_detectability_trough",
        f"{spring_carryover}_spring_carryover",
        f"{summer_suppression}_summer_suppression",
        f"{summer_decay}_summer_decay_acceleration",
        f"{pre_summer_retention}_pre_summer_retention",
        f"{autumn_component}_autumn_component",
        f"{year_end_component}_year_end_component",
        f"{response_dynamics}_response_dynamics",
    ]

    confidence = _classify_confidence(
        warnings, fit_score, baseline_presence, amplitude, options
    )

    summary = _build_summary(
        species_name=species_name,
        primary_class=primary_class,
        peak_month=peak_month,
        trough_month=trough_month,
        baseline_presence=baseline_presence,
        spring_carryover=spring_carryover,
        summer_suppression=summer_suppression,
        summer_decay=summer_decay,
        pre_summer_retention=pre_summer_retention,
    )

    return {
        "schema_version": "resident-classification/v1",
        "species": species_name,
        "model_family": "resident_detectability",
        "classification": {
            "primary_class": primary_class,
            "baseline_presence": baseline_presence,
            "detectability_peak_timing": peak_timing,
            "detectability_trough_timing": trough_timing,
            "spring_carryover": spring_carryover,
            "summer_suppression": summer_suppression,
            "summer_decay_acceleration": summer_decay,
            "pre_summer_retention": pre_summer_retention,
            "autumn_component": autumn_component,
            "year_end_component": year_end_component,
            "response_dynamics": response_dynamics,
            "traits": traits,
            "confidence": confidence,
        },
        "derived_metrics": {
            "target_peak_month": peak_month,
            "target_peak_label": MONTH_NAMES[peak_month],
            "target_trough_month": trough_month,
            "target_trough_label": MONTH_NAMES[trough_month],
            "target_peak_value": _decimal_to_float(peak_value),
            "target_trough_value": _decimal_to_float(trough_value),
            "target_mean_value": _decimal_to_float(mean_value),
            "target_amplitude": _decimal_to_float(amplitude),
            "baseline_to_peak_ratio": _decimal_to_float(
                _safe_ratio(p["BASELINE"], peak_value)
            ),
            "autumn_to_winter_weight_ratio": _decimal_to_float(
                _safe_ratio(p["AUTUMN_WEIGHT"], p["WINTER_WEIGHT"])
            ),
            "year_end_to_winter_weight_ratio": _decimal_to_float(
                _safe_ratio(p["YEAR_END_WEIGHT"], p["WINTER_WEIGHT"])
            ),
            "decay_to_growth_ratio": _decimal_to_float(
                _safe_ratio(p["DECAY_RATE"], p["GROWTH_RATE"])
            ),
            "monthly_target": {
                MONTH_NAMES[m]: _decimal_to_float(v) for m, v in monthly_target.items()
            },
        },
        "parameter_evidence": {
            name: _decimal_to_float(value) for name, value in p.items()
        },
        "fit": {"score": _coerce_json_value(fit_score)},
        "warnings": warnings,
        "summary": summary,
    }


def _normalise_parameters(parameters: Mapping[str, Any]) -> dict[str, Decimal]:
    """
    Validate and normalise required resident-model parameters

    :param parameters: Raw parameter mapping read from a fitted parameter JSON file or equivalent source
    :return: Dictionary containing each required parameter converted to ``Decimal``
    :raises ResidentClassificationError: If any required parameter is missing or cannot be converted
    """
    missing = [name for name in REQUIRED_PARAMETERS if name not in parameters]
    if missing:
        raise ResidentClassificationError(
            f"Missing required resident parameters: {', '.join(missing)}"
        )
    return {name: _to_decimal(parameters[name], name) for name in REQUIRED_PARAMETERS}


def _to_decimal(value: Any, name: str) -> Decimal:
    """
    Convert one raw parameter value to ``Decimal``

    :param value: Raw value to convert, usually a number or numeric string from JSON
    :param name: Parameter name used in error messages
    :return: Converted ``Decimal`` value
    :raises ResidentClassificationError: If conversion fails
    """
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise ResidentClassificationError(
            f"Parameter {name!r} cannot be converted to Decimal: {value!r}"
        ) from exc


def _validate_month(name: str, value: Decimal, warnings: list[str]) -> None:
    """
    Append a warning if a month-valued parameter lies outside the expected 1..12 range

    :param name: Name of the parameter being checked
    :param value: Month-like value to validate
    :param warnings: Mutable list that receives warning messages
    """
    if not (D("1") <= value <= D("12.999")):
        warnings.append(f"{name} lies outside the expected 1..12 month range.")


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    """
    Return a ratio while avoiding division by zero

    :param numerator: Value to divide
    :param denominator: Value to divide by
    :return: ``numerator / denominator`` when possible, otherwise ``Decimal("0")``
    """
    if denominator == 0:
        return D("0")
    return numerator / denominator


def _monthly_target_values(p: Mapping[str, Decimal]) -> dict[int, Decimal]:
    """
    Estimate monthly resident detectability target values from fitted parameters

    :param p: Normalised resident-model parameter mapping
    :return: Mapping of integer month number to derived target detectability value
    """
    values: dict[int, Decimal] = {}
    for month in range(1, 13):
        m = D(month)
        winter = _asymmetric_annual_bump(
            m, p["WINTER_PEAK"], p["WINTER_RISE_WIDTH"], p["WINTER_FALL_WIDTH"]
        )
        autumn = _asymmetric_annual_bump(
            m, p["AUTUMN_PEAK"], p["AUTUMN_RISE_WIDTH"], p["AUTUMN_FALL_WIDTH"]
        )
        autumn *= _autumn_onset_gate(m, p["AUTUMN_ONSET"], p["AUTUMN_GATE_SHARPNESS"])
        summer = _asymmetric_annual_bump(
            m, p["SUMMER_LOW"], p["SUMMER_RISE_WIDTH"], p["SUMMER_FALL_WIDTH"]
        )
        summer *= _logistic_onset_gate(m, p["SUMMER_ONSET"], p["SUMMER_GATE_SHARPNESS"])
        year_end = _asymmetric_annual_bump(
            m, p["YEAR_END_PEAK"], p["YEAR_END_RISE_WIDTH"], p["YEAR_END_FALL_WIDTH"]
        )
        spring_carryover = D("1") - _logistic_onset_gate(
            m, p["SPRING_CARRYOVER_END"], p["SPRING_CARRYOVER_SHARPNESS"]
        )

        target = (
            p["BASELINE"]
            + p["WINTER_WEIGHT"] * winter
            + p["AUTUMN_WEIGHT"] * autumn
            + p["YEAR_END_WEIGHT"] * year_end
            + p["SPRING_CARRYOVER_WEIGHT"] * spring_carryover
            - p["SUMMER_DIP"] * summer
        )
        values[month] = max(D("0"), target)
    return values


def _signed_month_distance(month: Decimal, peak: Decimal) -> Decimal:
    """
    Calculate circular signed distance from a seasonal peak

    :param month: Month being evaluated
    :param peak: Peak month used as the circular reference point
    :return: Signed shortest distance in months, in the range roughly -6..6
    """
    return (month - peak + D("6")) % D("12") - D("6")


def _asymmetric_annual_bump(
    month: Decimal, peak: Decimal, rise_width: Decimal, fall_width: Decimal
) -> Decimal:
    # Float maths is adequate for classification evidence. The solver remains Decimal-based
    """
    Evaluate an asymmetric circular seasonal bump

    :param month: Month being evaluated
    :param peak: Month at which the bump reaches its maximum
    :param rise_width: Exponent controlling the approach to the peak before/around the rising side
    :param fall_width: Exponent controlling the decline after/around the falling side
    :return: Bump strength between 0 and 1 as a ``Decimal``
    """
    angle = 2.0 * math.pi * (float(month) - float(peak)) / 12.0
    profile = (1.0 + math.cos(angle)) / 2.0
    if profile <= 0.0:
        return D("0")
    if profile >= 1.0:
        return D("1")
    delta = _signed_month_distance(month, peak)
    width = rise_width if delta <= 0 else fall_width
    return D(str(profile ** float(width)))


def _logistic_onset_gate(month: Decimal, onset: Decimal, sharpness: Decimal) -> Decimal:
    """
    Evaluate a logistic gate that turns on after a month threshold

    :param month: Month being evaluated
    :param onset: Month at which the gate begins opening
    :param sharpness: Steepness of the transition from closed to open
    :return: Gate value between 0 and 1 as a ``Decimal``
    """
    delta = _signed_month_distance(month, onset)
    x = float(sharpness * delta)
    if x > 40:
        return D("1")
    if x < -40:
        return D("0")
    return D(str(1.0 / (1.0 + math.exp(-x))))


def _autumn_onset_gate(month: Decimal, onset: Decimal, sharpness: Decimal) -> Decimal:
    """
    Evaluate an autumn-specific onset gate with year-end wrapping

    :param month: Month being evaluated
    :param onset: Month at which the autumn component begins to contribute
    :param sharpness: Steepness of the onset transition
    :return: Gate value between 0 and 1 as a ``Decimal``
    """
    x = float(sharpness * (month - onset))
    if x > 40:
        return D("1")
    if x < -40:
        return D("0")
    return D(str(1.0 / (1.0 + math.exp(-x))))


def _classify_baseline(
    baseline: Decimal,
	options: ResidentClassificationOptions
) -> str:
    """
    Classify persistent baseline detectability

    :param baseline: Fitted baseline value representing year-round detectability support
    :param options: Thresholds defining high, moderate, and low baseline labels
    :return: Baseline category label
    """
    if baseline >= options.high_baseline_min:
        return "strong"
    if baseline >= options.moderate_baseline_min:
        return "moderate"
    return "weak"


def _classify_spring_carryover(
    weight: Decimal,
	options: ResidentClassificationOptions
) -> str:
    """
    Classify the strength of spring carry-over

    :param weight: Fitted spring carry-over weight
    :param options: Thresholds defining strong, moderate, weak, and minimal labels
    :return: Spring carry-over category label
    """
    if weight >= options.strong_spring_carryover_min:
        return "strong"
    if weight >= options.moderate_spring_carryover_min:
        return "moderate"
    if weight > 0:
        return "weak"
    return "absent"


def _classify_summer_suppression(
    dip: Decimal,
	options: ResidentClassificationOptions
) -> str:
    """
    Classify the strength of summer detectability suppression

    :param dip: Fitted summer dip/suppression magnitude
    :param options: Thresholds defining strong, moderate, weak, and minimal labels
    :return: Summer suppression category label
    """
    if dip >= options.strong_summer_dip_min:
        return "strong"
    if dip >= options.moderate_summer_dip_min:
        return "moderate"
    if dip > 0:
        return "weak"
    return "absent"


def _classify_summer_decay(
    boost: Decimal,
	options: ResidentClassificationOptions
) -> str:
    """
    Classify acceleration of decay during summer

    :param boost: Fitted multiplier/boost applied to summer decay
    :param options: Thresholds defining strong, moderate, weak, and minimal labels
    :return: Summer decay acceleration category label
    """
    if boost >= options.strong_summer_decay_boost_min:
        return "strong"
    if boost >= options.moderate_summer_decay_boost_min:
        return "moderate"
    if boost > 0:
        return "weak"
    return "absent"


def _classify_pre_summer_retention(
    reduction: Decimal,
	options: ResidentClassificationOptions
) -> str:
    """
    Classify retention before the summer decline

    :param reduction: Fitted reduction in decay before summer, interpreted as persistence or carry-over retention
    :param options: Thresholds defining strong, moderate, weak, and minimal labels
    :return: Pre-summer retention category label
    """
    if reduction >= options.strong_pre_summer_retention_min:
        return "strong"
    if reduction >= options.moderate_pre_summer_retention_min:
        return "moderate"
    if reduction > 0:
        return "weak"
    return "absent"


def _classify_autumn_component(
    ratio: Decimal,
	options: ResidentClassificationOptions
) -> str:
    """
    Classify the relative autumn component strength

    :param ratio: Ratio of autumn support weight to winter support weight
    :param options: Thresholds defining meaningful, weak, and minimal autumn labels
    :return: Autumn component category label
    """
    if ratio >= options.meaningful_autumn_ratio_min:
        return "meaningful"
    if ratio >= options.weak_autumn_ratio_min:
        return "weak"
    return "minimal"


def _classify_year_end_component(
    ratio: Decimal,
	options: ResidentClassificationOptions
) -> str:
    """
    Classify the relative year-end component strength

    :param ratio: Ratio of year-end support weight to winter support weight
    :param options: Thresholds defining meaningful and minimal year-end labels
    :return: Year-end component category label
    """
    if ratio >= options.meaningful_year_end_ratio_min:
        return "meaningful"
    if ratio > 0:
        return "weak"
    return "absent"


def _classify_response_dynamics(
    growth: Decimal, decay: Decimal, summer_boost: Decimal
) -> str:
    """
    Classify fitted response dynamics from growth and decay terms

    :param growth: Fitted growth rate controlling how quickly detectability rises toward the target
    :param decay: Fitted ordinary decay rate controlling how quickly detectability falls
    :param summer_boost: Fitted additional summer decay boost
    :return: Response-dynamics category label
    """
    ratio = _safe_ratio(decay + summer_boost, growth)
    if ratio >= D("3"):
        return "rapid_decline_biased"
    if ratio >= D("2"):
        return "decline_biased"
    if ratio <= D("0.75"):
        return "growth_biased"
    return "balanced"


def _classify_timing(month_value: Decimal) -> str:
    """
    Convert a month-like value into a broad seasonal timing label

    :param month_value: Month value to classify
    :return: Timing category such as spring, summer, autumn, winter, or year-end
    """
    month = int(month_value.to_integral_value(rounding="ROUND_HALF_UP"))
    month = max(1, min(12, month))
    if month in (12, 1, 2):
        return "winter"
    if month in (3, 4):
        return "spring"
    if month in (5, 6):
        return "late_spring_early_summer"
    if month in (7, 8):
        return "summer"
    if month in (9, 10):
        return "autumn"
    return "late_autumn"


def _primary_class(
    *,
    baseline_presence: str,
    spring_carryover: str,
    summer_suppression: str,
    summer_decay: str,
    peak_timing: str,
    trough_timing: str,
) -> str:
    """
    Choose the main resident-model interpretation label from component classifications

    :param baseline_presence: Baseline presence category
    :param spring_carryover: Spring carry-over category
    :param summer_suppression: Summer suppression category
    :param summer_decay: Summer decay acceleration category
    :param peak_timing: Timing label for the fitted detectability peak
    :param trough_timing: Timing label for the fitted detectability trough
    :return: Primary resident detectability class label
    """
    if (
        summer_suppression == "strong"
        and summer_decay in ("strong", "moderate")
        and spring_carryover in ("strong", "moderate")
    ):
        return "resident_with_spring_persistence_and_summer_suppression"
    if summer_suppression in ("strong", "moderate") and summer_decay in (
        "strong",
        "moderate",
    ):
        return "resident_with_summer_detectability_collapse"
    if baseline_presence == "strong" and peak_timing in ("winter", "spring"):
        return "resident_with_winter_spring_detectability_peak"
    if baseline_presence == "weak":
        return "weak_baseline_resident_detectability_pattern"
    if trough_timing == "summer":
        return "resident_with_summer_detectability_trough"
    return "resident_with_seasonally_variable_detectability"


def _classify_confidence(
    warnings: list[str],
    fit_score: Any,
    baseline_presence: str,
    amplitude: Decimal,
    options: ResidentClassificationOptions,
) -> str:
    """
    Classify confidence in the resident-model interpretation

    :param warnings: Validation and plausibility warnings generated during classification
    :param fit_score: Optional model fit score; lower values are treated as better fits by the default thresholds
    :param baseline_presence: Baseline presence category used as supporting evidence
    :param amplitude: Difference between derived monthly target peak and trough
    :param options: Thresholds defining score bands and other confidence-related categories
    :return: Confidence label
    """
    if warnings:
        return "low"
    score = _try_decimal(fit_score)
    if score is not None:
        if score <= options.high_score_max:
            return "high"
        if score <= options.medium_score_max:
            return "medium"
        return "low"
    if baseline_presence == "weak" or amplitude < D("0.10"):
        return "medium"
    return "medium"


def _build_summary(
    *,
    species_name: str,
    primary_class: str,
    peak_month: int,
    trough_month: int,
    baseline_presence: str,
    spring_carryover: str,
    summer_suppression: str,
    summer_decay: str,
    pre_summer_retention: str,
) -> str:
    """
    Build a short prose summary for the resident-model classification

    :param species_name: Species name to mention in the summary
    :param primary_class: Primary class label selected for the species
    :param peak_month: Integer month number of the derived detectability peak
    :param trough_month: Integer month number of the derived detectability trough
    :param baseline_presence: Baseline presence category
    :param spring_carryover: Spring carry-over category
    :param summer_suppression: Summer suppression category
    :param summer_decay: Summer decay acceleration category
    :param pre_summer_retention: Pre-summer retention category
    :return: Human-readable one-paragraph summary
    """
    return (
        f"{species_name} is classified as {primary_class.replace('_', ' ')}. "
        f"The fitted resident detectability target peaks around {MONTH_NAMES[peak_month]} "
        f"and reaches its lowest point around {MONTH_NAMES[trough_month]}. "
        f"The model indicates {baseline_presence} baseline presence, {spring_carryover} spring carry-over, "
        f"{pre_summer_retention} pre-summer retention, {summer_suppression} summer suppression, "
        f"and {summer_decay} summer decay acceleration."
    )


def _decimal_to_float(value: Decimal) -> float:
    """
    Convert a ``Decimal`` to a JSON-friendly float

    :param value: Decimal value to convert
    :return: Float representation of ``value``
    """
    return float(value)


def _try_decimal(value: Any) -> Decimal | None:
    """
    Attempt to convert a value to ``Decimal`` without raising classification errors

    :param value: Raw value to convert
    :return: Converted ``Decimal`` or ``None`` if conversion fails
    """
    if value is None:
        return None
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError):
        return None


def _coerce_json_value(value: Any) -> Any:
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
