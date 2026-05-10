from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping, Optional

from seasonal.classification.utils import normalise_parameters
from seasonal.support.numeric import D, decimal_to_float
from seasonal.support.json import write_json, coerce_json_value
from seasonal.support.calendar import month_label


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
    """
    Thresholds used by the rule-based classifier

    These defaults are intentionally conservative and interpretable. They are
    expected to evolve as more species are fitted
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
    """Raised when seasonal model parameters cannot be classified"""


def classify_seasonal_model_to_json(
    parameters: Mapping[str, Any],
    output_path: str | Path,
    species: Optional[str] = None,
    score: Optional[Any] = None,
    options: SeasonalClassificationOptions | None = None,
    indent: int = 2
) -> dict[str, Any]:
    """
    Classify fitted seasonal-model parameters and write the classification JSON file

    :param parameters: Mapping of fitted seasonal model parameter names to values
    :param output_path: Destination path for the generated classification JSON file
    :param species: Species name to use in the output. If omitted, ``parameters["SPECIES"]`` is used
    :param score: Fit score to include in the output. If omitted, ``parameters["SCORE"]`` is used
    :param options: Threshold set controlling how numeric parameters are converted into categorical traits
    :param indent: JSON indentation level used when writing the output file
    :return: Classification dictionary
    """

    classification = classify_seasonal_model(
        parameters,
        species=species,
        score=score,
        options=options,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(output_path, classification, indent)

    return classification


def classify_seasonal_model(
    parameters: Mapping[str, Any],
    species: Optional[str] = None,
    score: Optional[Any] = None,
    options: SeasonalClassificationOptions | None = None,
) -> dict[str, Any]:
    """
    Classify fitted non-winter seasonal parameters into ecological traits

    :param parameters: Mapping of fitted seasonal model parameter names to values
    :param species: Species name to use in the output. If omitted, ``parameters["SPECIES"]`` is used
    :param score: Fit score used to derive a broad confidence label. If omitted, ``parameters["SCORE"]`` is used
    :param options: Threshold set controlling width, sharpness, decline, suppression, alignment, and confidence labels
    :return: Dictionary containing classification labels, derived metrics, parameter evidence, warnings, and a prose summary
    """

    options = options or SeasonalClassificationOptions()
    p = normalise_parameters(parameters, REQUIRED_PARAMETERS, SeasonalClassificationError)

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
            "season_start_month": decimal_to_float(start),
            "season_end_month": decimal_to_float(end),
            "forcing_peak_month": decimal_to_float(peak),
            "season_width_months": decimal_to_float(width),
            "season_midpoint_month": decimal_to_float(midpoint),
            "season_start_label": month_label(start),
            "season_end_label": month_label(end),
            "forcing_peak_label": month_label(peak),
        },
        "parameter_evidence": {
            name: decimal_to_float(value) for name, value in p.items()
        },
        "fit": {
            "score": coerce_json_value(fit_score),
        },
        "warnings": warnings,
        "summary": summary,
    }


def _classify_timing(peak: Decimal) -> str:
    """Classify the seasonal peak month into a broad timing label

    :param peak: Fitted forcing peak month
    :return: Timing category such as early_spring, spring, summer, autumn, or atypical
    """
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
    """
    Classify active season width

    :param width: Derived number of months from season start to season end, accounting for wrapping
    :param options: Thresholds defining narrow, moderate, broad, and very broad seasons
    :return: Season-width category label
    """
    if width <= options.narrow_width_max:
        return "narrow"
    if width <= options.moderate_width_max:
        return "moderate"
    if width <= options.broad_width_max:
        return "broad"
    return "very_broad"


def _classify_window_shape(sharpness: Decimal, options: SeasonalClassificationOptions) -> str:
    """
    Classify how sharply the seasonal activity window opens and closes

    :param sharpness: Fitted seasonal-window sharpness parameter
    :param options: Thresholds defining sharp, moderate, and gradual windows
    :return: Window-shape category label
    """
    if sharpness >= options.sharp_window_min:
        return "sharp"
    if sharpness <= options.gradual_window_max:
        return "gradual"
    return "moderate"


def _classify_decline(post_peak_decay: Decimal, options: SeasonalClassificationOptions) -> str:
    """
    Classify the strength of post-peak decline

    :param post_peak_decay: Fitted post-peak decay parameter
    :param options: Thresholds defining very strong, strong, moderate, and weak decline labels
    :return: Post-peak decline category label
    """
    if post_peak_decay >= options.strong_post_peak_decay_min:
        return "strong"
    if post_peak_decay >= options.moderate_post_peak_decay_min:
        return "moderate"
    return "weak"


def _classify_offseason_suppression(oos_decay: Decimal, options: SeasonalClassificationOptions) -> str:
    """
    Classify how strongly the model suppresses out-of-season presence

    :param oos_decay: Fitted out-of-season decay parameter
    :param options: Thresholds defining strong, moderate, and weak suppression labels
    :return: Off-season suppression category label
    """
    if oos_decay >= options.strong_oos_decay_min:
        return "strong"
    if oos_decay >= options.moderate_oos_decay_min:
        return "moderate"
    return "weak"


def _classify_peak_alignment(peak: Decimal, midpoint: Decimal, options: SeasonalClassificationOptions) -> str:
    """
    Classify whether the fitted peak is centred within the active season

    :param peak: Fitted forcing peak month
    :param midpoint: Derived midpoint of the active seasonal window
    :param options: Thresholds defining central, offset, and strongly offset peak alignment
    :return: Peak-alignment category label
    """
    delta = peak - midpoint
    if abs(delta) <= options.forcing_peak_tolerance:
        return "central"
    if delta < 0:
        return "early"
    return "late"


def _primary_class(timing: str, season_width: str) -> str:
    """
    Choose the main seasonal-model interpretation label

    :param timing: Broad timing category for the fitted seasonal peak
    :param season_width: Width category for the active season
    :return: Primary seasonal class label
    """
    if season_width == "narrow":
        return f"narrow_{timing}_seasonal_presence"
    if season_width == "moderate":
        return f"moderate_{timing}_seasonal_presence"
    return f"extended_{timing}_seasonal_presence"


def _classify_confidence(warnings: list[str], fit_score: Optional[Any], width: Decimal) -> str:
    """
    Classify confidence in the seasonal-model interpretation

    :param warnings: Validation and plausibility warnings generated during classification
    :param fit_score: Optional model fit score; lower values are treated as better fits by the default thresholds
    :param width: Derived active-season width in months
    :return: Confidence label
    """
    if warnings:
        return "review"

    # Optional, deliberately light-touch: score semantics may vary by pipeline
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
    species_name: str,
    primary_class: str,
    timing: str,
    season_width: str,
    window_shape: str,
    decline: str,
    offseason_suppression: str,
    start: Decimal,
    end: Decimal,
    peak: Decimal
) -> str:
    """
    Build a short prose summary for the seasonal-model classification

    :param species_name: Species name to mention in the summary
    :param primary_class: Primary class label selected for the species
    :param timing: Broad timing category for the fitted peak
    :param season_width: Width category for the active season
    :param window_shape: Sharpness category for the seasonal window
    :param decline: Post-peak decline category
    :param offseason_suppression: Out-of-season suppression category
    :param start: Fitted active-season start month
    :param end: Fitted active-season end month
    :param peak: Fitted forcing peak month
    :return: Human-readable one-paragraph summary
    """
    readable_class = primary_class.replace("_", " ")
    return (
        f"{species_name} is classified as {readable_class}. "
        f"The fitted seasonal window runs from about {month_label(start)} to {month_label(end)}, "
        f"with a {timing.replace('_', ' ')} peak around {month_label(peak)}. "
        f"The season is {season_width}, with a {window_shape} active window, "
        f"{decline} post-peak decline, and {offseason_suppression} off-season suppression."
    )
