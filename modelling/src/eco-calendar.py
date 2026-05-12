from __future__ import annotations

import argparse
from pathlib import Path

from seasonal.calendar.heatmap import plot_neighbourhood_calendar_heatmap
from seasonal.calendar.activity import build_neighbourhood_monthly_activity
from seasonal.calendar.loader import load_synthesised_species_data
from seasonal.calendar.extractor import extract_calendar_cluster_metadata
from seasonal.support.console import print_message
from seasonal.support.json import load_json


def main() -> None:
    """
    Main entry point for the feature, similarity and clustering pipeline
    """
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input-dirs", nargs="+", type=Path, required=True,
                        help="Directory containing simulated CSV files")
    parser.add_argument("-cl", "--clusters", type=Path, required=True, help="Cluster analysis JSON file path")
    parser.add_argument("-e", "--extracted", type=Path, required=True, help="Extracted cluster analysis JSON file path")
    parser.add_argument("-a", "--activity", type=Path, required=True, help="Monthly neighbourhood activity CSV file path")
    parser.add_argument("-hm", "--heatmap", type=Path, required=True,
                        help="Monthly neighbourhood activity heatmap PNG file path")
    args = parser.parse_args()

    # Load the cluster analysis JSON file and use it to generate the extracted details
    clusters = load_json(args.clusters)
    extracted = extract_calendar_cluster_metadata(clusters, args.extracted)
    print_message(f"Extracted clustering details written to {Path(args.extracted).name}")

    # Load the simulated CSV files for each species and build the monthly neighbourhood activity
    simulated = load_synthesised_species_data(args.input_dirs)
    activity = build_neighbourhood_monthly_activity(simulated, extracted, args.activity)
    print_message(f"Neighbourhood activity details written to {Path(args.activity).name}")

    # Generate the heatmap
    plot_neighbourhood_calendar_heatmap(activity, args.heatmap)
    print_message(f"Neighbourhood activity heatmap written to {Path(args.heatmap).name}")


if __name__ == "__main__":
    main()
