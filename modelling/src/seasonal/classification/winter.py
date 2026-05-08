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
    "BASELINE",
    "WINTER_WEIGHT",
    "AUTUMN_WEIGHT",
    "WINTER_PEAK",
    "AUTUMN_PEAK",
    "WINTER_WIDTH",
    "AUTUMN_WIDTH",
    "SUMMER_DIP",
    "SUMMER_LOW",
    "SUMMER_WIDTH",
]


@dataclass(frozen=True)
class WinterClassificationOptions:
    """Thresholds used by the rule-based winter model classifier.

    These defaults are deliberately conservative and are intended to be tuned
    after you have seen outputs across more fitted species.
    """

    strong_autumn_ratio_min: Decimal = D("0.50")
    moderate_autumn_ratio_min: Decimal = D("0.20")
    weak_autumn_ratio_min: Decimal = D("0.05")

    strong_summer_dip_min: Decimal = D("0.25")
    moderate_summer_dip_min: Decimal = D("0.10")

    low_baseline_max: Decimal = D("0.05")
    moderate_baseline_max: Decimal = D("0.20")

    fast_decay_min: Decimal = D("2.0")
    slow_growth_max: Decimal = D("1.0")

    broad_bump_width_max: Decimal = D("2.5")      # lower exponent = broader bump
    narrow_bump_width_min: Decimal = D("4.0")     # higher exponent = narrower bump

    high_score_max: Decimal = D("0.075")
    medium_score_max: Decimal = D("0.15")


class WinterClassificationError(ValueError):
    """Raised when winter model parameters cannot be classified."""


def classify_winter_model_to_json(
    parameters: Mapping[str, Any],
    output_path: str | Path,
    species: Optional[str] = None,
    score: Optional[Any] = None,
    options: WinterClassificationOptions | None = None,
    indent: int = 2,
) -> dict[str, Any]:
    """Classify a fitted winter model and write the classification JSON file."""

    classification = classify_winter_model(
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


def classify_winter_model(
    parameters: Mapping[str, Any],
    *,
    species: Optional[str] = None,
    score: Optional[Any] = None,
    options: WinterClassificationOptions | None = None,
) -> dict[str, Any]:
    """Classify a fitted winter visitor model and return a JSON-serialisable dict."""

    options = options or WinterClassificationOptions()
    p = _normalise_parameters(parameters)

    species_name = species or str(parameters.get("SPECIES", "Unknown species"))
    fit_score = score if score is not None else parameters.get("SCORE")

    warnings: list[str] = []
    _validate_month("WINTER_PEAK", p["WINTER_PEAK"], warnings)
    _validate_month("AUTUMN_PEAK", p["AUTUMN_PEAK"], warnings)
    _validate_month("SUMMER_LOW", p["SUMMER_LOW"], warnings)

    if p["WINTER_WEIGHT"] <= 0:
        warnings.append("Winter weight is zero or negative; expected a positive winter component.")
    if p["AUTUMN_WEIGHT"] < 0:
        warnings.append("Autumn weight is negative; expected zero or positive autumn component.")
    if p["SUMMER_DIP"] < 0:
        warnings.append("Summer dip is negative; expected zero or positive summer suppression.")

    autumn_ratio = _safe_ratio(p["AUTUMN_WEIGHT"], p["WINTER_WEIGHT"])
    decay_growth_ratio = _safe_ratio(p["DECAY_RATE"], p["GROWTH_RATE"])

    monthly_target = _monthly_target_values(p)
    peak_month = max(monthly_target, key=monthly_target.get)
    trough_month = min(monthly_target, key=monthly_target.get)
    active_months = [m for m, v in monthly_target.items() if v >= D("0.10")]

    timing = _classify_winter_timing(p["WINTER_PEAK"])
    autumn_component = _classify_autumn_component(autumn_ratio, options)
    summer_suppression = _classify_summer_suppression(p["SUMMER_DIP"], p["BASELINE"], options)
    baseline_presence = _classify_baseline(p["BASELINE"], options)
    winter_shape = _classify_bump_width(p["WINTER_WIDTH"], options)
    autumn_shape = _classify_bump_width(p["AUTUMN_WIDTH"], options)
    response_dynamics = _classify_response_dynamics(p["GROWTH_RATE"], p["DECAY_RATE"], options)

    primary_class = _primary_class(autumn_component, baseline_presence)

    traits = [
        "year_wrapping_winter_presence",
        f"{timing}_winter_peak",
        f"{autumn_component}_autumn_component",
        f"{summer_suppression}_summer_suppression",
        f"{baseline_presence}_baseline_presence",
        f"{winter_shape}_winter_bump",
        f"{response_dynamics}_response_dynamics",
    ]

    confidence = _classify_confidence(warnings, fit_score, p)

    summary = _build_summary(
        species_name=species_name,
        primary_class=primary_class,
        winter_peak=p["WINTER_PEAK"],
        autumn_peak=p["AUTUMN_PEAK"],
        autumn_component=autumn_component,
        summer_low=p["SUMMER_LOW"],
        summer_suppression=summer_suppression,
        baseline_presence=baseline_presence,
        response_dynamics=response_dynamics,
    )

    return {
        "schema_version": "winter-classification/v1",
        "species": species_name,
        "model_family": "winter_presence",
        "classification": {
            "primary_class": primary_class,
            "winter_timing": timing,
            "autumn_component": autumn_component,
            "summer_suppression": summer_suppression,
            "baseline_presence": baseline_presence,
            "winter_bump_shape": winter_shape,
            "autumn_bump_shape": autumn_shape,
            "response_dynamics": response_dynamics,
            "traits": traits,
            "confidence": confidence,
        },
        "derived_metrics": {
            "winter_peak_month": _decimal_to_float(p["WINTER_PEAK"]),
            "winter_peak_label": _month_label(p["WINTER_PEAK"]),
            "autumn_peak_month": _decimal_to_float(p["AUTUMN_PEAK"]),
            "autumn_peak_label": _month_label(p["AUTUMN_PEAK"]),
            "summer_low_month": _decimal_to_float(p["SUMMER_LOW"]),
            "summer_low_label": _month_label(p["SUMMER_LOW"]),
            "autumn_to_winter_weight_ratio": _decimal_to_float(autumn_ratio),
            "decay_to_growth_ratio": _decimal_to_float(decay_growth_ratio),
            "target_peak_month": peak_month,
            "target_peak_label": MONTH_NAMES[peak_month],
            "target_trough_month": trough_month,
            "target_trough_label": MONTH_NAMES[trough_month],
            "active_months_ge_0_10": active_months,
            "monthly_target": {MONTH_NAMES[m]: _decimal_to_float(v) for m, v in monthly_target.items()},
        },
        "parameter_evidence": {
            name: _decimal_to_float(value) for name, value in p.items()
        },
        "fit": {
            "score": _coerce_json_value(fit_score),
        },
        "warnings": warnings,
        "summary": summary,
    }


def _normalise_parameters(parameters: Mapping[str, Any]) -> dict[str, Decimal]:
    missing = [name for name in REQUIRED_PARAMETERS if name not in parameters]
    if missing:
        raise WinterClassificationError(f"Missing required winter parameters: {', '.join(missing)}")

    return {name: _to_decimal(parameters[name], name) for name in REQUIRED_PARAMETERS}


def _to_decimal(value: Any, name: str) -> Decimal:
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise WinterClassificationError(f"Parameter {name!r} cannot be converted to Decimal: {value!r}") from exc


def _validate_month(name: str, value: Decimal, warnings: list[str]) -> None:
    if not (D("1") <= value <= D("12")):
        warnings.append(f"{name} lies outside the expected 1..12 month range.")


def _safe_ratio(numerator: Decimal, denominator: Decimal) -> Decimal:
    if denominator == 0:
        return D("0")
    return numerator / denominator


def _monthly_target_values(p: Mapping[str, Decimal]) -> dict[int, Decimal]:
    values: dict[int, Decimal] = {}
    for month in range(1, 13):
        m = D(month)
        winter = _annual_bump(m, p["WINTER_PEAK"], p["WINTER_WIDTH"])
        autumn = _annual_bump(m, p["AUTUMN_PEAK"], p["AUTUMN_WIDTH"])
        summer = _annual_bump(m, p["SUMMER_LOW"], p["SUMMER_WIDTH"])
        target = (
            p["BASELINE"]
            + p["WINTER_WEIGHT"] * winter
            + p["AUTUMN_WEIGHT"] * autumn
            - p["SUMMER_DIP"] * summer
        )
        values[month] = max(D("0"), target)
    return values


def _annual_bump(month: Decimal, peak: Decimal, width: Decimal) -> Decimal:
    # Float maths is sufficient here: this is only for classification evidence,
    # not for solving the ODE. The model itself remains Decimal-based.
    angle = 2.0 * math.pi * (float(month) - float(peak)) / 12.0
    profile = (1.0 + math.cos(angle)) / 2.0
    if profile <= 0.0:
        return D("0")
    if profile >= 1.0:
        return D("1")
    return D(str(profile ** float(width)))


def _classify_winter_timing(winter_peak: Decimal) -> str:
    month = _rounded_month(winter_peak)
    if month in (12, 1, 2):
        return "core_winter"
    if month == 3:
        return "late_winter_early_spring"
    if month == 11:
        return "early_winter"
    return "atypical"


def _classify_autumn_component(autumn_ratio: Decimal, options: WinterClassificationOptions) -> str:
    if autumn_ratio >= options.strong_autumn_ratio_min:
        return "strong"
    if autumn_ratio >= options.moderate_autumn_ratio_min:
        return "moderate"
    if autumn_ratio >= options.weak_autumn_ratio_min:
        return "weak"
    return "minimal"


def _classify_summer_suppression(
    summer_dip: Decimal,
    baseline: Decimal,
    options: WinterClassificationOptions,
) -> str:
    if summer_dip >= options.strong_summer_dip_min:
        return "strong"
    if summer_dip >= options.moderate_summer_dip_min:
        return "moderate"
    if baseline <= options.low_baseline_max:
        return "implicit_low_baseline"
    return "weak"


def _classify_baseline(baseline: Decimal, options: WinterClassificationOptions) -> str:
    if baseline <= options.low_baseline_max:
        return "low"
    if baseline <= options.moderate_baseline_max:
        return "moderate"
    return "high"


def _classify_bump_width(width: Decimal, options: WinterClassificationOptions) -> str:
    # In the model, this is an exponent on the bump: lower = broader, higher = narrower.
    if width <= options.broad_bump_width_max:
        return "broad"
    if width >= options.narrow_bump_width_min:
        return "narrow"
    return "moderate"


def _classify_response_dynamics(
    growth_rate: Decimal,
    decay_rate: Decimal,
    options: WinterClassificationOptions,
) -> str:
    if growth_rate <= options.slow_growth_max and decay_rate >= options.fast_decay_min:
        return "slow_arrival_fast_departure"
    if decay_rate >= growth_rate * D("2"):
        return "faster_departure_than_arrival"
    if growth_rate >= decay_rate * D("2"):
        return "faster_arrival_than_departure"
    return "balanced"


def _primary_class(autumn_component: str, baseline_presence: str) -> str:
    if baseline_presence == "high":
        return "winter_weighted_resident_like_presence"
    if autumn_component in ("strong", "moderate"):
        return "winter_visitor_with_autumn_arrival_component"
    if autumn_component == "weak":
        return "winter_visitor_with_weak_autumn_arrival_component"
    return "winter_visitor"


def _classify_confidence(
    warnings: list[str],
    fit_score: Optional[Any],
    p: Mapping[str, Decimal],
) -> str:
    if warnings:
        return "review"

    if p["WINTER_WEIGHT"] <= 0:
        return "review"

    if fit_score is not None:
        try:
            score_d = Decimal(str(fit_score))
            if score_d <= WinterClassificationOptions().high_score_max:
                return "high"
            if score_d <= WinterClassificationOptions().medium_score_max:
                return "medium"
            return "low"
        except (InvalidOperation, TypeError):
            pass

    return "medium"


def _build_summary(
    *,
    species_name: str,
    primary_class: str,
    winter_peak: Decimal,
    autumn_peak: Decimal,
    autumn_component: str,
    summer_low: Decimal,
    summer_suppression: str,
    baseline_presence: str,
    response_dynamics: str,
) -> str:
    readable_class = primary_class.replace("_", " ")
    return (
        f"{species_name} is classified as {readable_class}. "
        f"The fitted winter component peaks around {_month_label(winter_peak)}, "
        f"with a {autumn_component} autumn component centred around {_month_label(autumn_peak)}. "
        f"The model has {baseline_presence} baseline presence and {summer_suppression} summer suppression "
        f"centred around {_month_label(summer_low)}. "
        f"The fitted response dynamics suggest {response_dynamics.replace('_', ' ')}."
    )


def _rounded_month(value: Decimal) -> int:
    rounded = int(value.to_integral_value(rounding="ROUND_HALF_UP"))
    return max(1, min(12, rounded))


def _month_label(value: Decimal) -> str:
    return MONTH_NAMES[_rounded_month(value)]


def _decimal_to_float(value: Decimal) -> float:
    return float(value)


def _coerce_json_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    try:
        return float(value)
    except (TypeError, ValueError):
        return value
