from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Optional

from seasonal.support.utils import D
from seasonal.support.calendar import MONTH_NAMES


REQUIRED_PARAMETERS = [
    "GROWTH",
    "DECAY",
    "OOS_DECAY",
    "POST_PEAK_DECAY",
    "POST_PEAK_SHARPNESS",
    "SEASON_START",
    "SEASON_END",
    "SHARPNESS",
    "FORCING_PEAK",
]


@dataclass(frozen=True)
class SeasonalClassificationOptions:
    """Thresholds used by the rule-based classifier.

    These defaults are intentionally conservative and interpretable. They are
    expected to evolve as more species are fitted.
    """

    narrow_width_max: Decimal = D("2.0")
    moderate_width_max: Decimal = D("4.0")
    broad_width_max: Decimal = D("6.0")

    sharp_window_min: Decimal = D("8.0")
    gradual_window_max: Decimal = D("4.0")

    strong_post_peak_decay_min: Decimal = D("3.5")
    moderate_post_peak_decay_min: Decimal = D("2.0")

    strong_oos_decay_min: Decimal = D("4.0")
    moderate_oos_decay_min: Decimal = D("2.0")

    forcing_peak_tolerance: Decimal = D("0.75")


class SeasonalClassificationError(ValueError):
    """Raised when seasonal model parameters cannot be classified."""


def classify_seasonal_model_to_json(
    parameters: Mapping[str, Any],
    output_path: str | Path,
    *,
    species: Optional[str] = None,
    score: Optional[Any] = None,
    options: SeasonalClassificationOptions | None = None,
    indent: int = 2,
) -> dict[str, Any]:
    """Classify a fitted seasonal model and write the classification JSON file.

    Parameters
    ----------
    parameters:
        Mapping containing the seasonal model parameters. Values may be strings,
        floats, ints, or Decimals. The function expects the same parameter names
        used by the seasonal ODE model JSON files.
    output_path:
        Path to write the JSON classification artefact.
    species:
        Optional species name. If omitted, uses parameters["SPECIES"] when present.
    score:
        Optional fit score supplied by the fitting pipeline. If omitted, uses
        parameters["SCORE"] when present.
    options:
        Optional threshold set for classification rules.
    indent:
        JSON indentation level.

    Returns
    -------
    dict
        The classification document that was written to disk.
    """

    classification = classify_seasonal_model(
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


def classify_seasonal_model(
    parameters: Mapping[str, Any],
    species: Optional[str] = None,
    score: Optional[Any] = None,
    options: SeasonalClassificationOptions | None = None,
) -> dict[str, Any]:
    """Classify a fitted seasonal model and return a JSON-serialisable dict."""

    options = options or SeasonalClassificationOptions()
    p = _normalise_parameters(parameters)

    species_name = species or str(parameters.get("SPECIES", "Unknown species"))
    fit_score = score if score is not None else parameters.get("SCORE")

    start = p["SEASON_START"]
    end = p["SEASON_END"]
    peak = p["FORCING_PEAK"]
    width = end - start
    midpoint = (start + end) / D("2")

    warnings: list[str] = []
    if width <= 0:
        warnings.append("Season end is not later than season start; this classifier expects a non-wrapping seasonal model.")
    if not (D("1") <= peak <= D("12")):
        warnings.append("Forcing peak lies outside the expected 1..12 month range.")
    if peak < start or peak > end:
        warnings.append("Forcing peak lies outside the fitted seasonal window.")

    timing = _classify_timing(peak)
    season_width = _classify_width(width, options)
    window_shape = _classify_window_shape(p["SHARPNESS"], options)
    decline = _classify_decline(p["POST_PEAK_DECAY"], options)
    offseason_suppression = _classify_offseason_suppression(p["OOS_DECAY"], options)
    peak_alignment = _classify_peak_alignment(peak, midpoint, options)

    traits = [
        f"{timing}_peak",
        f"{season_width}_season",
        f"{window_shape}_seasonal_window",
        f"{decline}_post_peak_decline",
        f"{offseason_suppression}_offseason_suppression",
        f"{peak_alignment}_peak_alignment",
    ]

    primary_class = _primary_class(timing, season_width)
    confidence = _classify_confidence(warnings, fit_score, width)

    summary = _build_summary(
        species_name=species_name,
        primary_class=primary_class,
        timing=timing,
        season_width=season_width,
        window_shape=window_shape,
        decline=decline,
        offseason_suppression=offseason_suppression,
        start=start,
        end=end,
        peak=peak,
    )

    return {
        "schema_version": "seasonal-classification/v1",
        "species": species_name,
        "model_family": "seasonal_presence",
        "classification": {
            "primary_class": primary_class,
            "timing": timing,
            "season_width": season_width,
            "window_shape": window_shape,
            "post_peak_decline": decline,
            "offseason_suppression": offseason_suppression,
            "peak_alignment": peak_alignment,
            "traits": traits,
            "confidence": confidence,
        },
        "derived_metrics": {
            "season_start_month": _decimal_to_float(start),
            "season_end_month": _decimal_to_float(end),
            "forcing_peak_month": _decimal_to_float(peak),
            "season_width_months": _decimal_to_float(width),
            "season_midpoint_month": _decimal_to_float(midpoint),
            "season_start_label": _month_label(start),
            "season_end_label": _month_label(end),
            "forcing_peak_label": _month_label(peak),
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
        raise SeasonalClassificationError(f"Missing required seasonal parameters: {', '.join(missing)}")

    return {name: _to_decimal(parameters[name], name) for name in REQUIRED_PARAMETERS}


def _to_decimal(value: Any, name: str) -> Decimal:
    try:
        return value if isinstance(value, Decimal) else Decimal(str(value))
    except (InvalidOperation, TypeError) as exc:
        raise SeasonalClassificationError(f"Parameter {name!r} cannot be converted to Decimal: {value!r}") from exc


def _classify_timing(peak: Decimal) -> str:
    month = int(peak.to_integral_value(rounding="ROUND_HALF_UP"))
    month = max(1, min(12, month))

    if month in (1, 2):
        return "winter"
    if month == 3:
        return "early_spring"
    if month in (4, 5):
        return "spring"
    if month in (6, 7, 8):
        return "summer"
    if month in (9, 10):
        return "autumn"
    return "late_autumn_winter"


def _classify_width(width: Decimal, options: SeasonalClassificationOptions) -> str:
    if width <= options.narrow_width_max:
        return "narrow"
    if width <= options.moderate_width_max:
        return "moderate"
    if width <= options.broad_width_max:
        return "broad"
    return "very_broad"


def _classify_window_shape(sharpness: Decimal, options: SeasonalClassificationOptions) -> str:
    if sharpness >= options.sharp_window_min:
        return "sharp"
    if sharpness <= options.gradual_window_max:
        return "gradual"
    return "moderate"


def _classify_decline(post_peak_decay: Decimal, options: SeasonalClassificationOptions) -> str:
    if post_peak_decay >= options.strong_post_peak_decay_min:
        return "strong"
    if post_peak_decay >= options.moderate_post_peak_decay_min:
        return "moderate"
    return "weak"


def _classify_offseason_suppression(oos_decay: Decimal, options: SeasonalClassificationOptions) -> str:
    if oos_decay >= options.strong_oos_decay_min:
        return "strong"
    if oos_decay >= options.moderate_oos_decay_min:
        return "moderate"
    return "weak"


def _classify_peak_alignment(
    peak: Decimal,
    midpoint: Decimal,
    options: SeasonalClassificationOptions,
) -> str:
    delta = peak - midpoint
    if abs(delta) <= options.forcing_peak_tolerance:
        return "central"
    if delta < 0:
        return "early"
    return "late"


def _primary_class(timing: str, season_width: str) -> str:
    if season_width == "narrow":
        return f"narrow_{timing}_seasonal_presence"
    if season_width == "moderate":
        return f"moderate_{timing}_seasonal_presence"
    return f"extended_{timing}_seasonal_presence"


def _classify_confidence(warnings: list[str], fit_score: Optional[Any], width: Decimal) -> str:
    if warnings:
        return "review"

    # Optional, deliberately light-touch: score semantics may vary by pipeline.
    if fit_score is not None:
        try:
            score_d = Decimal(str(fit_score))
            if score_d <= D("0.075"):
                return "high"
            if score_d <= D("0.15"):
                return "medium"
            return "low"
        except (InvalidOperation, TypeError):
            pass

    if width <= 0:
        return "review"
    return "medium"


def _build_summary(
    *,
    species_name: str,
    primary_class: str,
    timing: str,
    season_width: str,
    window_shape: str,
    decline: str,
    offseason_suppression: str,
    start: Decimal,
    end: Decimal,
    peak: Decimal,
) -> str:
    readable_class = primary_class.replace("_", " ")
    return (
        f"{species_name} is classified as {readable_class}. "
        f"The fitted seasonal window runs from about {_month_label(start)} to {_month_label(end)}, "
        f"with a {timing.replace('_', ' ')} peak around {_month_label(peak)}. "
        f"The season is {season_width}, with a {window_shape} active window, "
        f"{decline} post-peak decline, and {offseason_suppression} off-season suppression."
    )


def _month_label(value: Decimal) -> str:
    rounded = int(value.to_integral_value(rounding="ROUND_HALF_UP"))
    rounded = max(1, min(12, rounded))
    return MONTH_NAMES[rounded]


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
