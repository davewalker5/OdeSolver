from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from seasonal.support.calendar import month_label
from seasonal.support.json import load_json, write_json


CORE_COLUMNS = [
    "species",
    "model_family",
    "schema_version",
    "primary_class",
    "confidence",
    "fit_score",
    "n_warnings",

    # Harmonised timing features
    "peak_month",
    "peak_label",
    "trough_month",
    "trough_label",
    "season_start_month",
    "season_start_label",
    "season_end_month",
    "season_end_label",
    "season_width_months",
    "season_midpoint_month",

    # Harmonised behavioural / shape features
    "baseline_presence",
    "timing",
    "season_width_class",
    "window_shape",
    "post_peak_decline",
    "offseason_suppression",
    "summer_suppression",
    "autumn_component",
    "response_dynamics",

    # Derived numeric comparators
    "target_mean_value",
    "target_amplitude",
    "baseline_to_peak_ratio",
    "autumn_to_winter_weight_ratio",
    "year_end_to_winter_weight_ratio",
    "decay_to_growth_ratio",
    "active_month_count_ge_0_10",

    # Trait handling
    "traits",
    "trait_count",

    # Provenance
    "source_file",
    "summary",
]


def print_message(message):
    """
    Show a timestamped message

    :param message: Message text
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} : {message}")


def print_error(message):
    """
    Show a timestamped error message

    :param message: Message text
    """
    print_message(f"ERROR: {message}")


def first_present(mapping: Dict[str, Any], keys: Iterable[str]) -> Any:
    """
    Return the first non-null value found for a sequence of keys

    :param mapping: Source mapping to search
    :param keys: Ordered keys to test
    :return: First present non-null value or None
    """
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def normalise_traits(classification: Dict[str, Any]) -> List[str]:
    """
    Normalise classification trait values to a list of strings

    :param classification: Classification block from a species record
    :return: List of trait strings
    """
    traits = classification.get("traits", [])
    if traits is None:
        return []
    if not isinstance(traits, list):
        return [str(traits)]
    return [str(t) for t in traits]


def harmonise_peak_month(model_family: str, derived: Dict[str, Any]) -> Any:
    """
    Pick a comparable peak month across model families

    For resident and winter models, target_peak_month represents the peak of the fitted monthly
    target curve. For seasonal visitors, forcing_peak_month is the most comparable value

    :param model_family: Model family identifier
    :param derived: Derived metrics block
    :return: Harmonised peak month value
    """
    if model_family == "seasonal_presence":
        return first_present(derived, ["forcing_peak_month", "target_peak_month"])
    return first_present(derived, ["target_peak_month", "winter_peak_month", "forcing_peak_month"])


def harmonise_peak_label(model_family: str, derived: Dict[str, Any], peak_month: Any) -> Optional[str]:
    """
    Pick a comparable peak month label across model families

    :param model_family: Model family identifier
    :param derived: Derived metrics block
    :param peak_month: Harmonised peak month value
    :return: Harmonised peak month label
    """
    if model_family == "seasonal_presence":
        label = first_present(derived, ["forcing_peak_label", "target_peak_label"])
    else:
        label = first_present(derived, ["target_peak_label", "winter_peak_label", "forcing_peak_label"])
    return label or month_label(peak_month)


def extract_feature_record(path: Path, data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract a harmonised feature record from a classification JSON structure

    :param path: Source classification file path
    :param data: Loaded classification JSON data
    :return: Harmonised feature record
    """
    classification = data.get("classification", {}) or {}
    derived = data.get("derived_metrics", {}) or {}
    fit = data.get("fit", {}) or {}
    warnings = data.get("warnings", []) or []
    model_family = data.get("model_family")

    traits = normalise_traits(classification)

    peak_month = harmonise_peak_month(str(model_family), derived)
    peak_label = harmonise_peak_label(str(model_family), derived, peak_month)

    active_months = derived.get("active_months_ge_0_10")
    active_month_count = len(active_months) if isinstance(active_months, list) else None

    # These are intentionally broad and sparse. Not every model family has
    # every feature; missing values are expected and useful
    record: Dict[str, Any] = {
        "species": data.get("species"),
        "model_family": model_family,
        "schema_version": data.get("schema_version"),
        "primary_class": classification.get("primary_class"),
        "confidence": classification.get("confidence"),
        "fit_score": fit.get("score"),
        "n_warnings": len(warnings),

        "peak_month": peak_month,
        "peak_label": peak_label,
        "trough_month": first_present(derived, ["target_trough_month", "summer_low_month"]),
        "trough_label": first_present(derived, ["target_trough_label", "summer_low_label"]),
        "season_start_month": derived.get("season_start_month"),
        "season_start_label": derived.get("season_start_label"),
        "season_end_month": derived.get("season_end_month"),
        "season_end_label": derived.get("season_end_label"),
        "season_width_months": derived.get("season_width_months"),
        "season_midpoint_month": derived.get("season_midpoint_month"),

        "baseline_presence": classification.get("baseline_presence"),
        "timing": first_present(classification, ["timing", "winter_timing", "detectability_peak_timing"]),
        "season_width_class": classification.get("season_width"),
        "window_shape": classification.get("window_shape"),
        "post_peak_decline": classification.get("post_peak_decline"),
        "offseason_suppression": classification.get("offseason_suppression"),
        "summer_suppression": classification.get("summer_suppression"),
        "autumn_component": classification.get("autumn_component"),
        "response_dynamics": classification.get("response_dynamics"),

        "target_mean_value": derived.get("target_mean_value"),
        "target_amplitude": derived.get("target_amplitude"),
        "baseline_to_peak_ratio": derived.get("baseline_to_peak_ratio"),
        "autumn_to_winter_weight_ratio": derived.get("autumn_to_winter_weight_ratio"),
        "year_end_to_winter_weight_ratio": derived.get("year_end_to_winter_weight_ratio"),
        "decay_to_growth_ratio": derived.get("decay_to_growth_ratio"),
        "active_month_count_ge_0_10": active_month_count,

        "traits": traits,
        "trait_count": len(traits),

        "source_file": str(path),
        "summary": data.get("summary"),
    }

    return record


def flatten_for_csv(record: Dict[str, Any]) -> Dict[str, Any]:
    """
    Flatten complex record fields into CSV-friendly values

    :param record: Feature record
    :return: Flattened record suitable for CSV output
    """
    flat = dict(record)
    flat["traits"] = ";".join(record.get("traits", []))
    return flat


def build_feature_table(input_paths: List[Path]) -> Dict[str, Any]:
    """
    Build the complete feature matrix from classification files

    :param input_paths: Input classification JSON paths
    :return: Feature matrix structure
    """
    records: List[Dict[str, Any]] = []
    source_files: List[str] = []

    for path in sorted(input_paths):
        data = load_json(path)
        records.append(extract_feature_record(path, data))
        source_files.append(str(path))

    return {
        "schema_version": "species-feature-table/v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "description": (
            "Whole-set seasonal ecology feature table compiled from "
            "per-species classification JSON files."
        ),
        "n_species": len(records),
        "source_files": source_files,
        "features": records,
    }


def write_csv(path: Path, records: List[Dict[str, Any]]) -> None:
    """
    Write feature records to a human-readable CSV file

    :param path: Output CSV path
    :param records: Feature records to write
    """
    path.parent.mkdir(parents=True, exist_ok=True)

    # Keep core columns first, then include any future extra keys at the end
    all_keys = set()
    for record in records:
        all_keys.update(record.keys())

    extra_columns = sorted(k for k in all_keys if k not in CORE_COLUMNS)
    fieldnames = CORE_COLUMNS + extra_columns

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for record in records:
            writer.writerow(flatten_for_csv(record))


def find_input_files(input_dirs: list[Path]) -> List[Path]:
    """
    Find classification JSON files within input directories

    :param input_dirs: Directories to search
    :return: De-duplicated list of classification file paths
    """
    paths: List[Path] = []
    for input_dir in input_dirs:
        paths.extend(input_dir.glob("*_classification.json"))

    # De-duplicate while preserving sorted deterministic output later
    unique = {p.resolve(): p for p in paths}
    return list(unique.values())


def main() -> None:
    """
    Main entry point for the feature matrix builder
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dirs", nargs="+", type=Path, required=True,
                        help="Directory containing classification JSON files")
    parser.add_argument("-oj", "--output-json", type=Path, required=True, help="Canonical JSON output path")
    parser.add_argument("-oc", "--output-csv", type=Path, help="Companion CSV output path. Use --no-csv to skip")
    args = parser.parse_args()

    # Look for JSON classification files in the specified input folders
    input_files = find_input_files(args.input_dirs)
    if not input_files:
        print_error("No classification JSON files found")
        return

    # Build the feature maxtrix
    print_message(f"Building feature matrix from {len(input_files)} classification files")
    feature_matrix = build_feature_table(input_files)
    print_message(f"Feature matrix contains {feature_matrix['n_species']} species")

    # Write the matrix to the canonical JSON file
    write_json(args.output_json, feature_matrix)
    print_message(f"Feature matrix written to {Path(args.output_json).name}")

    # If requested, write the human-friendly CSV file
    if args.output_csv:
        write_csv(args.output_csv, feature_matrix["features"])
        print_message(f"Feature matrix written to {Path(args.output_csv).name}")


if __name__ == "__main__":
    main()
