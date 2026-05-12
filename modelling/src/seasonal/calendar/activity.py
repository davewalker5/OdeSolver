from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Any

from seasonal.support.json import write_json
from seasonal.support.calendar import month_label


def build_neighbourhood_monthly_activity(
    synthesised_rows: list[dict[str, Any]],
    calendar_clusters: dict[str, Any],
    output_path: str | Path,
    value_column: str = "synthesised",
    month_column: str = "month",
) -> dict[str, Any]:
    """
    Build monthly activity summaries for each seasonal ecological neighbourhood.

    :param synthesised_rows: Simulated output for all species scaled to observed data scale
    :param calendar_clusters: Extracted cluser information taking from the clustering analysis
    :param output_path: Path to the output activity JSON file to create
    :param value_column: Name of the "value" column in synthesised_rows
    :param month_column: Name of the "month" column in synthesised_rows
    :return: Dictionary of neighbourhood monthly activity data
    """

    species_to_cluster = _build_species_to_cluster_lookup(calendar_clusters)

    species_max_values = _calculate_species_max_values(
        synthesised_rows,
        value_column=value_column,
    )

    grouped_values: dict[tuple[int, int], list[float]] = defaultdict(list)

    for row in synthesised_rows:
        species = row.get("Species")
        if not species or species not in species_to_cluster:
            continue

        month = _parse_month(row.get(month_column))
        if month is None:
            continue

        raw_value = _parse_float(row.get(value_column))
        if raw_value is None:
            continue

        max_value = species_max_values.get(species)
        if not max_value or max_value <= 0:
            continue

        cluster_id = species_to_cluster[species]
        normalised_value = raw_value / max_value

        grouped_values[(cluster_id, month)].append(normalised_value)

    output_clusters: list[dict[str, Any]] = []

    for cluster in sorted(
        calendar_clusters.get("clusters", []),
        key=lambda c: c.get("cluster_id", 0),
    ):
        cluster_id = cluster["cluster_id"]

        monthly_activity: list[dict[str, Any]] = []

        for month in range(1, 13):
            values = grouped_values.get((cluster_id, month), [])
            mean_activity = sum(values) / len(values) if values else 0.0

            monthly_activity.append(
                {
                    "month": month,
                    "month_name": month_label(month),
                    "mean_activity": round(mean_activity, 6),
                    "n_species_contributing": len(values),
                }
            )

        output_clusters.append(
            {
                "cluster_id": cluster_id,
                "calendar_label": cluster.get(
                    "calendar_label",
                    f"Cluster {cluster_id}",
                ),
                "n_species": cluster.get(
                    "n_species",
                    len(cluster.get("species", [])),
                ),
                "species": cluster.get("species", []),
                "monthly_activity": monthly_activity,
            }
        )

    output = {
        "schema_version": "seasonal-ecological-calendar-activity/v1",
        "source_cluster_schema_version": calendar_clusters.get("schema_version"),
        "n_clusters": len(output_clusters),
        "normalisation": {
            "method": "species_max",
            "description": (
                "Each species is normalised to its own maximum synthesised value "
                "before cluster-level monthly aggregation."
            ),
            "value_column": value_column,
        },
        "clusters": output_clusters,
    }

    write_json(output_path, output)

    return output


def _build_species_to_cluster_lookup(calendar_clusters: dict[str, Any]) -> dict[str, int]:
    """
    Build a lookup between a species and the ID for the cluster it belongs to

    :param calendar_clusters: Extracted cluser information taking from the clustering analysis
    :return: Dictionary of species/cluster ID mappings
    """
    species_to_cluster: dict[str, int] = {}

    for cluster in calendar_clusters.get("clusters", []):
        cluster_id = cluster["cluster_id"]

        for species in cluster.get("species", []):
            species_to_cluster[species] = cluster_id

    return species_to_cluster


def _calculate_species_max_values(synthesised_rows: list[dict[str, Any]], value_column: str) -> dict[str, float]:
    """
    Build a lookup between a species and its maximum activity value

    :param synthesised_rows: Simulated output for all species scaled to observed data scale
    :return: Dictionary of species/maximum activity mappings
    """
    species_max_values: dict[str, float] = {}

    for row in synthesised_rows:
        species = row.get("Species")
        value = _parse_float(row.get(value_column))

        if not species or value is None:
            continue

        current_max = species_max_values.get(species, 0.0)
        species_max_values[species] = max(current_max, value)

    return species_max_values


def _parse_month(value: Any) -> int | None:
    """
    Parse a month number from a value
    
    :param value: Value to parse
    :return: Month number or None
    """
    try:
        month = int(value)
    except (TypeError, ValueError):
        return None

    if 1 <= month <= 12:
        return month

    return None


def _parse_float(value: Any) -> float | None:
    """
    Parse a float from a value
    
    :param value: Value to parse
    :return: Floating point value or None
    """
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
