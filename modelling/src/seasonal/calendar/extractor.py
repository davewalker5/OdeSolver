from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def extract_calendar_cluster_metadata(
    cluster_analysis: dict[str, Any],
    output_path: str | Path,
) -> dict[str, Any]:
    """
    Extract lightweight cluster metadata for seasonal ecological calendar generation

    This deliberately keeps only the fields needed to group species into calendar neighbourhoods
    and label them for downstream visualisation

    :param cluster_analysis: Data loaded from th cluster analysis JSON output
    :return: Simplified, extracted information
    """

    clusters = cluster_analysis.get("clusters", [])

    extracted_clusters: list[dict[str, Any]] = []

    for cluster in clusters:
        species = cluster.get("species", [])

        extracted_clusters.append(
            {
                "cluster_id": cluster.get("cluster_id"),
                "calendar_label": _suggest_calendar_label(cluster),
                "description": cluster.get("description", ""),
                "n_species": cluster.get("n_species", len(species)),
                "species": species,
            }
        )

    extracted = {
        "schema_version": "seasonal-ecological-calendar-clusters/v1",
        "source_schema_version": cluster_analysis.get("schema_version"),
        "source_created_utc": cluster_analysis.get("created_utc"),
        "n_species": cluster_analysis.get("n_species"),
        "n_clusters": cluster_analysis.get("n_clusters", len(extracted_clusters)),
        "cluster_caveat": (
            cluster_analysis
            .get("method", {})
            .get("cluster_caveat", "")
        ),
        "clusters": extracted_clusters,
    }

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", encoding="utf-8") as f:
        json.dump(extracted, f, indent=2, ensure_ascii=False)

    return extracted


def _suggest_calendar_label(cluster: dict[str, Any]) -> str:
    """
    Generate a short, readable calendar label from cluster metadata

    :param cluster: Dictionary containing the cluster properties for a single cluster
    :return: Suggested cluster name
    """

    species = cluster.get("species", [])
    n_species = cluster.get("n_species", len(species))
    dominant_class = cluster.get("dominant_primary_class")

    if n_species == 1 and species:
        return f"{species[0]} neighbourhood"

    if dominant_class:
        return dominant_class.replace("_", " ").title()

    cluster_id = cluster.get("cluster_id", "unknown")
    return f"Cluster {cluster_id}"
