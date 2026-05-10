from __future__ import annotations

import argparse
from pathlib import Path

from seasonal.features.species_similarity import build_species_similarity
from seasonal.features.feature_matrix import build_feature_table, find_input_files, write_csv
from seasonal.support.console import print_error, print_message
from seasonal.support.json import write_json


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


def main() -> None:
    """
    Main entry point for the feature matrix builder
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dirs", nargs="+", type=Path, required=True,
                        help="Directory containing classification JSON files")
    parser.add_argument("-oj", "--output-json", type=Path, required=True, help="Canonical feature matrix JSON output path")
    parser.add_argument("-oc", "--output-csv", type=Path, help="Companion CSV output path. Use --no-csv to skip")
    parser.add_argument("-oss", "--output-species-similarity", type=Path, required=True,
                        help="Species similarity JSON output path")
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
        write_csv(args.output_csv, feature_matrix["features"], CORE_COLUMNS)
        print_message(f"Feature matrix written to {Path(args.output_csv).name}")

    # Build the species similarity matrix
    build_species_similarity(feature_matrix, args.output_species_similarity)
    print_message(f"Species similarity written to {Path(args.output_species_similarity).name}")


if __name__ == "__main__":
    main()
