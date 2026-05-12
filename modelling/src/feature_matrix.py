from __future__ import annotations

import argparse
from pathlib import Path

from seasonal.features.species_similarity import build_species_similarity, save_similarity_summary
from seasonal.features.similarity_heatmap import generate_species_similarity_heatmap
from seasonal.features.similarity_clusters import extract_species_similarity_clusters, save_cluster_summary
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
    parser.add_argument("-j", "--json", type=Path, required=True, help="Canonical feature matrix JSON output path")
    parser.add_argument("-c", "--csv", type=Path, help="Companion CSV output path. Use --no-csv to skip")
    parser.add_argument("-s", "--similarity", type=Path, required=True, help="Species similarity output path")
    parser.add_argument("-ssu", "--similarity-summary", type=Path, help="Species similarity summary output file path")
    parser.add_argument("-hm", "--heatmap", type=Path, required=True,
                        help="Species similarity summary heatmap image file path")
    parser.add_argument("-cl", "--clusters", type=Path, required=True, help="Cluster analysis output file path")
    parser.add_argument("-csu", "--cluster-summary", type=Path, required=True,
                        help="Cluster analysis summary output file path")
    parser.add_argument("-d", "--dendrogram", type=Path, required=True,
                        help="Species similarity summary dendogram image file path")
    args = parser.parse_args()

    # Look for JSON classification files in the specified input folders
    input_files = find_input_files(args.input_dirs)
    if not input_files:
        print_error("No classification JSON files found")
        return

    # Build the feature matrix
    print_message(f"Building feature matrix from {len(input_files)} classification files")
    feature_matrix = build_feature_table(input_files)
    print_message(f"Feature matrix contains {feature_matrix['n_species']} species")

    # Write the matrix to the canonical JSON file
    write_json(args.json, feature_matrix)
    print_message(f"Feature matrix written to {Path(args.json).name}")

    # If requested, write the human-friendly CSV file
    if args.csv:
        write_csv(args.csv, feature_matrix["features"], CORE_COLUMNS)
        print_message(f"Feature matrix written to {Path(args.csv).name}")

    # Build the species similarity matrix
    similarity = build_species_similarity(feature_matrix, args.similarity)
    print_message(f"Species similarity written to {Path(args.similarity).name}")
    if args.similarity_summary:
        save_similarity_summary(similarity, args.similarity_summary)
        print_message(f"Species similarity text dump written to {Path(args.similarity_summary).name}")

    # Generate the species similarity heatmap
    generate_species_similarity_heatmap(similarity, args.heatmap)
    print_message(f"Species similarity heatmap written to {Path(args.heatmap).name}")

    # Extract the species similarity clusters
    clusters = extract_species_similarity_clusters(similarity, feature_matrix, args.clusters, n_clusters=8)
    print_message(f"Species similarity cluster analysis written to {Path(args.clusters).name}")
    if args.cluster_summary:
        save_cluster_summary(clusters, args.cluster_summary)
        print_message(f"Species similarity text dump written to {Path(args.cluster_summary).name}")


if __name__ == "__main__":
    main()
