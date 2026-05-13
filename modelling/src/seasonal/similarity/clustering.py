from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

import numpy as np
from scipy.cluster.hierarchy import fcluster
from seasonal.support.clustering import order_species_by_linkage, serialise_linkage_matrix
from seasonal.similarity.similarity import build_similarity_matrix, extract_species_names
from seasonal.support.numeric import round_float, safe_float
from seasonal.support.calendar import circular_month_mean, signed_circular_month_difference, month_label


DEFAULT_NUMERIC_FEATURES = [
    "peak_month",
    "trough_month",
    "season_start_month",
    "season_end_month",
    "season_width_months",
    "season_midpoint_month",
    "target_mean_value",
    "target_amplitude",
    "baseline_to_peak_ratio",
    "autumn_to_winter_weight_ratio",
    "year_end_to_winter_weight_ratio",
    "decay_to_growth_ratio",
    "active_month_count_ge_0_10",
    "fit_score",
]

DEFAULT_CATEGORICAL_FEATURES = [
    "model_family",
    "primary_class",
    "confidence",
    "baseline_presence",
    "timing",
    "season_width_class",
    "window_shape",
    "post_peak_decline",
    "offseason_suppression",
    "summer_suppression",
    "autumn_component",
    "response_dynamics",
]

MONTH_FEATURES = {
    "peak_month",
    "trough_month",
    "season_start_month",
    "season_end_month",
    "season_midpoint_month",
}


GENERATED_SCHEMA_VERSION = "species-similarity-clusters/v2"


def extract_species_similarity_clusters(
    similarity_data: Dict[str, Any],
    feature_matrix: Dict[str, Any],
    output_path: str | Path | None = None,
    n_clusters: int = 6,
    distance_threshold: float | None = None,
    linkage_method: str = "average",
    numeric_features: Optional[Sequence[str]] = None,
    categorical_features: Optional[Sequence[str]] = None,
    top_n_traits: int = 10,
    top_n_distinguishing_features: int = 8
) -> Dict[str, Any]:
    """
    Extract and summarise species clusters from a pairwise similarity dataset

    The function uses the same broad idea as the clustered heatmap: convert
    similarity to distance, run hierarchical clustering, cut the resulting tree,
    then summarise each cluster using the original species feature matrix

    :param similarity_data: Species similarity dictionary
    :param feature_matrix: Species feature matrix
    :param output_path: Optional JSON file path
    :param n_clusters: Number of clusters to extract when distance_threshold is not set
    :param distance_threshold: Distance cutoff threshold. Lower values produce tighter clusters
    :param linkage_method: Average is a good default for ecological similarity structures
    :param numeric_features: Numeric feature names to summarise
    :param categorical_features: Categorical feature names to summarise
    :param top_n_traits: Number of common traits to retain for each cluster
    :param top_n_distinguishing_features: Number of numeric features with the strongest cluster-vs-global
        contrast to retain for each cluster
    :return: Dictionary containing cluster membership, summaries and provenance
    """
    numeric_features = list(numeric_features or DEFAULT_NUMERIC_FEATURES)
    categorical_features = list(categorical_features or DEFAULT_CATEGORICAL_FEATURES)

    species_names = extract_species_names(similarity_data)
    features_by_species = _extract_features_by_species(feature_matrix)
    _validate_species_coverage(species_names, features_by_species)

    similarity_matrix = build_similarity_matrix(species_names, similarity_data)
    leaf_order, linkage_matrix = order_species_by_linkage(similarity_matrix, linkage_method=linkage_method)
    linkage_details = serialise_linkage_matrix(
        linkage_matrix=linkage_matrix,
        species_names=species_names,
        leaf_order=leaf_order,
    )

    if distance_threshold is not None:
        raw_labels = fcluster(linkage_matrix, t=distance_threshold, criterion="distance")
        cluster_cut = {
            "criterion": "distance",
            "distance_threshold": distance_threshold,
        }
    else:
        raw_labels = fcluster(linkage_matrix, t=n_clusters, criterion="maxclust")
        cluster_cut = {
            "criterion": "maxclust",
            "n_clusters_requested": n_clusters,
        }

    # Renumber clusters according to heatmap/dendrogram leaf order. This makes
    # cluster IDs visually stable and easier to compare with the heatmap
    label_to_ordered_id: Dict[int, int] = {}
    next_cluster_id = 1
    for species_index in leaf_order:
        label = int(raw_labels[species_index])
        if label not in label_to_ordered_id:
            label_to_ordered_id[label] = next_cluster_id
            next_cluster_id += 1

    species_cluster_ids = {
        species_names[i]: label_to_ordered_id[int(raw_labels[i])]
        for i in range(len(species_names))
    }

    global_numeric_summary = _summarise_numeric_features(
        [features_by_species[name] for name in species_names],
        numeric_features,
    )

    clusters = []
    for cluster_id in sorted(set(species_cluster_ids.values())):
        ordered_species = [species_names[i] for i in leaf_order]
        members = [
            name for name in ordered_species
            if species_cluster_ids[name] == cluster_id]
        member_features = [features_by_species[name] for name in members]

        clusters.append(
            _summarise_cluster(
                cluster_id=cluster_id,
                members=members,
                member_features=member_features,
                numeric_features=numeric_features,
                categorical_features=categorical_features,
                global_numeric_summary=global_numeric_summary,
                top_n_traits=top_n_traits,
                top_n_distinguishing_features=top_n_distinguishing_features,
            )
        )

    result: Dict[str, Any] = {
        "schema_version": GENERATED_SCHEMA_VERSION,
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_similarity_schema_version": similarity_data.get("schema_version"),
        "source_feature_schema_version": feature_matrix.get("schema_version"),
        "n_species": len(species_names),
        "n_clusters": len(clusters),
        "method": {
            "description": "Hierarchical clustering over pairwise species similarity, "
            "followed by cluster-level summaries from the species feature matrix.",
            "linkage_method": linkage_method,
            "cluster_cut": cluster_cut,
            "distance_definition": "distance = 1 - similarity",
            "cluster_caveat": "Clusters should be interpreted as exploratory seasonal "
            "assemblages rather than fixed ecological categories.",
        },
        "species_order": [species_names[i] for i in leaf_order],
        "linkage": linkage_details,
        "species_cluster_ids": species_cluster_ids,
        "clusters": clusters,
    }

    if output_path is not None:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def _extract_features_by_species(feature_matrix: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    """
    Build a per-species dictionary of features where the species name is the key

    :param feature_matrix: Species feature matrix
    :return: Dictionary of species features
    """
    features = feature_matrix.get("features")
    if not isinstance(features, list) or not features:
        raise ValueError("feature_matrix must contain a non-empty 'features' list")

    result: Dict[str, Dict[str, Any]] = {}
    for record in features:
        if not isinstance(record, dict) or not record.get("species"):
            raise ValueError("Each feature record must be a dictionary with a 'species' value")
        species = str(record["species"])
        if species in result:
            raise ValueError(f"Duplicate feature record for species: {species}")
        result[species] = record

    return result


def _validate_species_coverage(species_names: Sequence[str], features_by_species: Dict[str, Dict[str, Any]]) -> None:
    """
    Make sure all species are represented in the species features dictionary

    :param species_names: List of species names
    :return: Dictionary of species features
    """
    missing = [name for name in species_names if name not in features_by_species]
    if missing:
        message = f"feature_matrix is missing feature records for: {', '.join(missing)}"
        raise ValueError(message)


def _summarise_cluster(
    cluster_id: int,
    members: List[str],
    member_features: List[Dict[str, Any]],
    numeric_features: Sequence[str],
    categorical_features: Sequence[str],
    global_numeric_summary: Dict[str, Dict[str, Any]],
    top_n_traits: int,
    top_n_distinguishing_features: int,
) -> Dict[str, Any]:
    """
    Build a summary dictionary for one extracted species cluster

    :param cluster_id: Ordered cluster identifier assigned after dendrogram leaf ordering
    :param members: Species names belonging to the cluster, already ordered for display
    :param member_features: Feature records for the species in the cluster
    :param numeric_features: Numeric feature names to summarise for the cluster
    :param categorical_features: Categorical feature names to summarise for the cluster
    :param global_numeric_summary: Numeric summaries calculated across all species, used for
        cluster-vs-global comparisons
    :param top_n_traits: Maximum number of common traits to include in the summary
    :param top_n_distinguishing_features: Maximum number of cluster-vs-global numeric contrasts
        to include in the summary
    :return: Dictionary containing membership, dominant classes, feature summaries, common traits
        and suggested label terms for the cluster
    """
    numeric_summary = _summarise_numeric_features(member_features, numeric_features)
    categorical_summary = _summarise_categorical_features(member_features, categorical_features)
    common_traits = _summarise_traits(member_features, top_n=top_n_traits)
    distinguishing_numeric_features = _summarise_distinguishing_numeric_features(
        cluster_summary=numeric_summary,
        global_summary=global_numeric_summary,
        top_n=top_n_distinguishing_features,
    )

    description = _describe_cluster(
        members=members,
        categorical_summary=categorical_summary,
        numeric_summary=numeric_summary,
        common_traits=common_traits,
        distinguishing_numeric_features=distinguishing_numeric_features,
    )

    return {
        "cluster_id": cluster_id,
        "n_species": len(members),
        "species": members,
        "description": description,
        "dominant_model_family": _dominant_value(categorical_summary.get("model_family")),
        "dominant_primary_class": _dominant_value(categorical_summary.get("primary_class")),
        "numeric_summary": numeric_summary,
        "categorical_summary": categorical_summary,
        "common_traits": common_traits,
        "distinguishing_numeric_features": distinguishing_numeric_features,
        "suggested_label_terms": _suggest_label_terms(
            categorical_summary=categorical_summary,
            numeric_summary=numeric_summary,
            common_traits=common_traits,
        ),
    }


def _describe_cluster(
    members: Sequence[str],
    categorical_summary: Dict[str, Dict[str, Any]],
    numeric_summary: Dict[str, Dict[str, Any]],
    common_traits: Sequence[Dict[str, Any]],
    distinguishing_numeric_features: Sequence[Dict[str, Any]],
) -> str:
    """
    Generate a compact human-readable interpretation of a cluster.

    The description is deliberately deterministic and evidence-based: it only
    uses the cluster summaries already present in the JSON, rather than trying
    to infer taxonomy or causal ecology.
    """
    n_members = len(members)
    model_family = _dominant_value(categorical_summary.get("model_family"))
    primary_class = _dominant_value(categorical_summary.get("primary_class"))
    timing = _dominant_value(categorical_summary.get("timing"))
    width_class = _dominant_value(categorical_summary.get("season_width_class"))
    window_shape = _dominant_value(categorical_summary.get("window_shape"))
    baseline = _dominant_value(categorical_summary.get("baseline_presence"))
    summer_suppression = _dominant_value(categorical_summary.get("summer_suppression"))
    autumn_component = _dominant_value(categorical_summary.get("autumn_component"))
    response = _dominant_value(categorical_summary.get("response_dynamics"))

    opening = _cluster_opening_sentence(
        members=members,
        model_family=model_family,
        primary_class=primary_class,
        timing=timing,
    )

    details: List[str] = []

    peak = _summary_mean(numeric_summary, "peak_month")
    start = _summary_mean(numeric_summary, "season_start_month")
    end = _summary_mean(numeric_summary, "season_end_month")
    width = _summary_mean(numeric_summary, "season_width_months")
    trough = _summary_mean(numeric_summary, "trough_month")

    if model_family == "seasonal_presence":
        seasonal_bits: List[str] = []
        if start is not None and end is not None:
            seasonal_bits.append(
                f"the fitted active window runs roughly from {month_label(start)} to {month_label(end)}"
            )
        if peak is not None:
            seasonal_bits.append(f"with a mean peak around {month_label(peak)}")
        if width is not None:
            seasonal_bits.append(f"and an average width of {width:.1f} months")
        if seasonal_bits:
            details.append(_sentence_from_bits(seasonal_bits))

        shape_bits = []
        if width_class:
            shape_bits.append(f"{_humanise_token(width_class)} season")
        if window_shape:
            shape_bits.append(f"{_humanise_token(window_shape)} active window")
        if shape_bits:
            details.append("It is characterised by " + " and ".join(shape_bits) + ".")

    elif model_family == "resident_detectability":
        seasonal_bits = []
        if peak is not None:
            seasonal_bits.append(f"detectability peaks around {month_label(peak)}")
        if trough is not None:
            seasonal_bits.append(f"and is lowest around {month_label(trough)}")
        if seasonal_bits:
            details.append(_sentence_from_bits(seasonal_bits))

        dynamics_bits = []
        if baseline:
            dynamics_bits.append(f"{_humanise_token(baseline)} baseline presence")
        if summer_suppression:
            dynamics_bits.append(f"{_humanise_token(summer_suppression)} summer suppression")
        if autumn_component:
            dynamics_bits.append(f"{_humanise_token(autumn_component)} autumn component")
        if response:
            dynamics_bits.append(f"{_humanise_token(response)} response dynamics")
        if dynamics_bits:
            details.append("The shared pattern includes " + _join_phrase(dynamics_bits) + ".")

    elif model_family == "winter_presence":
        winter_bits = []
        if peak is not None:
            winter_bits.append(f"a winter peak around {month_label(peak)}")
        if autumn_component:
            winter_bits.append(f"a {_humanise_token(autumn_component)} autumn component")
        if summer_suppression:
            winter_bits.append(f"{_humanise_token(summer_suppression)} summer suppression")
        if response:
            winter_bits.append(f"{_humanise_token(response)} response dynamics")
        if winter_bits:
            details.append("The defining pattern is " + _join_phrase(winter_bits) + ".")

    else:
        if peak is not None:
            details.append(f"The mean fitted peak is around {month_label(peak)}.")

    trait_phrase = _common_trait_phrase(common_traits, n_members)
    if trait_phrase:
        details.append(trait_phrase)

    contrast_phrase = _distinguishing_feature_phrase(distinguishing_numeric_features)
    if contrast_phrase:
        details.append(contrast_phrase)

    return " ".join([opening] + details)


def _cluster_opening_sentence(
    members: Sequence[str],
    model_family: Optional[str],
    primary_class: Optional[str],
    timing: Optional[str],
) -> str:
    """
    Build the opening sentence for a human-readable cluster description

    :param members: Species names belonging to the cluster
    :param model_family: Dominant model family for the cluster, if available
    :param primary_class: Dominant primary classification for the cluster, if available
    :param timing: Dominant timing category for the cluster, if available
    :return: Opening sentence describing the cluster at a high level
    """
    if len(members) == 1:
        subject = f"Single-species cluster containing {members[0]}"
    else:
        subject = f"Cluster of {len(members)} species"

    descriptors = []
    if timing:
        # This results in a duplication of the season that looks odd
        # descriptors.append(_humanise_token(timing))
        pass

    if primary_class:
        descriptors.append(_humanise_token(primary_class))
    elif model_family:
        descriptors.append(_humanise_token(model_family))

    if descriptors:
        return subject + ", mainly representing " + " ".join(descriptors) + "."
    return subject + "."


def _summary_mean(summary: Dict[str, Dict[str, Any]], feature: str) -> Optional[float]:
    """
    Extract the mean value for a feature from a numeric summary dictionary

    :param summary: Numeric summary dictionary keyed by feature name
    :param feature: Feature name whose mean value should be returned
    :return: Mean value as a float, or None if unavailable or not numeric
    """
    value = summary.get(feature, {}).get("mean")
    return safe_float(value)


def _humanise_token(value: str) -> str:
    """
    Convert an underscore-delimited token into readable text

    :param value: Machine-readable token or classification value
    :return: Human-readable version of the token
    """
    return value.replace("_", " ")


def _sentence_from_bits(bits: Sequence[str]) -> str:
    """
    Join sentence fragments and format them as a sentence

    :param bits: Ordered sentence fragments to combine
    :return: Capitalised sentence ending with a full stop, or an empty string
    """
    if not bits:
        return ""
    text = _join_phrase(list(bits))
    return text[:1].upper() + text[1:] + "."


def _join_phrase(items: Sequence[str]) -> str:
    """
    Join a sequence of phrases using readable comma-and conjunction formatting

    :param items: Phrases to combine
    :return: Human-readable joined phrase
    """
    items = [str(item) for item in items if item]
    if not items:
        return ""
    if len(items) == 1:
        return items[0]
    if len(items) == 2:
        return f"{items[0]} and {items[1]}"
    return ", ".join(items[:-1]) + f", and {items[-1]}"


def _common_trait_phrase(common_traits: Sequence[Dict[str, Any]], n_members: int) -> Optional[str]:
    """
    Build a sentence describing high-support traits shared by cluster members.

    :param common_traits: Ordered trait summary dictionaries for the cluster
    :param n_members: Number of species in the cluster
    :return: Human-readable trait sentence, or None if no high-support traits are present
    """
    high_support_traits = []
    for row in common_traits:
        trait = row.get("trait")
        fraction = safe_float(row.get("fraction"))
        if trait and fraction is not None and fraction >= 0.75:
            high_support_traits.append(_humanise_token(str(trait)))
        if len(high_support_traits) >= 3:
            break

    if not high_support_traits:
        return None

    if n_members == 1:
        return "Its defining traits include " + _join_phrase(high_support_traits) + "."
    return "Common high-support traits include " + _join_phrase(high_support_traits) + "."


def _distinguishing_feature_phrase(distinguishing_numeric_features: Sequence[Dict[str, Any]]) -> Optional[str]:
    """
    Build a sentence describing the strongest numeric contrasts for a cluster

    :param distinguishing_numeric_features: Ordered cluster-vs-global numeric contrast dictionaries
    :return: Human-readable contrast sentence, or None if no strong contrasts are present
    """
    strong = []
    for row in distinguishing_numeric_features:
        feature = row.get("feature")
        direction = row.get("direction")
        scaled = safe_float(row.get("scaled_difference"))
        if not feature or direction not in {"higher", "lower"} or scaled is None:
            continue
        if abs(scaled) < 0.25:
            continue
        strong.append(f"{_humanise_token(str(feature))} is {direction} than the whole-set average")
        if len(strong) >= 2:
            break

    if not strong:
        return None

    return "Compared with the full species set, " + _join_phrase(strong) + "."


def _summarise_numeric_features(
    records: Sequence[Dict[str, Any]],
    feature_names: Sequence[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Calculate count, mean and range statistics for selected numeric features

    Month-like features are averaged with a circular mean so that values around
    December and January remain close to each other

    :param records: Species feature records to summarise
    :param feature_names: Numeric feature names to extract from each record
    :return: Dictionary keyed by feature name, containing n, mean, min and max
    """
    summary: Dict[str, Dict[str, Any]] = {}

    for feature in feature_names:
        values = [safe_float(record.get(feature)) for record in records]
        values = [value for value in values if value is not None]

        if not values:
            continue

        if feature in MONTH_FEATURES:
            mean_value = circular_month_mean(values)
        else:
            mean_value = float(np.mean(values))

        summary[feature] = {
            "n": len(values),
            "mean": round_float(mean_value),
            "min": round_float(float(np.min(values))),
            "max": round_float(float(np.max(values))),
        }

    return summary


def _summarise_categorical_features(
    records: Sequence[Dict[str, Any]],
    feature_names: Sequence[str],
) -> Dict[str, Dict[str, Any]]:
    """
    Count categorical feature values and identify the dominant value for each feature

    :param records: Species feature records to summarise
    :param feature_names: Categorical feature names to extract from each record
    :return: Dictionary keyed by feature name, including the dominant value, dominant count,
        dominant fraction and a full ordered value-count breakdown
    """
    summary: Dict[str, Dict[str, Any]] = {}
    n_records = len(records)

    for feature in feature_names:
        values = [record.get(feature) for record in records]
        values = [str(value) for value in values if value not in (None, "")]

        if not values:
            continue

        counts = Counter(values)
        ordered = counts.most_common()
        summary[feature] = {
            "dominant": ordered[0][0],
            "dominant_count": ordered[0][1],
            "dominant_fraction": round_float(ordered[0][1] / n_records),
            "values": [
                {
                    "value": value,
                    "count": count,
                    "fraction": round_float(count / n_records),
                }
                for value, count in ordered
            ],
        }

    return summary


def _summarise_traits(records: Sequence[Dict[str, Any]], *, top_n: int) -> List[Dict[str, Any]]:
    """
    Count recurring trait labels across a set of species feature records

    :param records: Species feature records, each optionally containing a traits list
    :param top_n: Maximum number of most common traits to return
    :return: Ordered list of trait summary dictionaries containing trait, count and fraction
    """
    counter: Counter[str] = Counter()
    n_records = len(records)

    for record in records:
        traits = record.get("traits") or []
        if not isinstance(traits, list):
            continue
        counter.update(str(trait) for trait in traits)

    return [
        {
            "trait": trait,
            "count": count,
            "fraction": round_float(count / n_records),
        }
        for trait, count in counter.most_common(top_n)
    ]


def _summarise_distinguishing_numeric_features(
    cluster_summary: Dict[str, Dict[str, Any]],
    global_summary: Dict[str, Dict[str, Any]],
    top_n: int,
) -> List[Dict[str, Any]]:
    """
    Identify numeric features where a cluster differs most strongly from the global mean

    Differences are scaled by the global feature range so features with different units can be
    ranked together. Month-like features use signed circular differences

    :param cluster_summary: Numeric summary for one cluster
    :param global_summary: Numeric summary across all species
    :param top_n: Maximum number of distinguishing features to return
    :return: Ordered list of feature contrast dictionaries, strongest absolute scaled difference first
    """
    rows: List[Dict[str, Any]] = []

    for feature, cluster_stats in cluster_summary.items():
        global_stats = global_summary.get(feature)
        if not global_stats:
            continue

        cluster_mean = safe_float(cluster_stats.get("mean"))
        global_mean = safe_float(global_stats.get("mean"))
        global_min = safe_float(global_stats.get("min"))
        global_max = safe_float(global_stats.get("max"))

        if cluster_mean is None or global_mean is None or global_min is None or global_max is None:
            continue

        global_range = global_max - global_min
        if global_range == 0:
            continue

        if feature in MONTH_FEATURES:
            raw_difference = signed_circular_month_difference(cluster_mean, global_mean)
        else:
            raw_difference = cluster_mean - global_mean

        scaled_difference = raw_difference / global_range

        rows.append(
            {
                "feature": feature,
                "cluster_mean": round_float(cluster_mean),
                "global_mean": round_float(global_mean),
                "difference": round_float(raw_difference),
                "scaled_difference": round_float(scaled_difference),
                "direction": "higher" if raw_difference > 0 else "lower",
            }
        )

    rows.sort(key=lambda row: abs(float(row["scaled_difference"])), reverse=True)
    return rows[:top_n]


def _suggest_label_terms(
    categorical_summary: Dict[str, Dict[str, Any]],
    numeric_summary: Dict[str, Dict[str, Any]],
    common_traits: Sequence[Dict[str, Any]],
) -> List[str]:
    """
    Provide evidence-based label hints without attempting to generate a final
    ecological interpretation
    """
    terms: List[str] = []

    for feature in ["model_family", "timing", "season_width_class", "primary_class"]:
        dominant = _dominant_value(categorical_summary.get(feature))
        if dominant:
            terms.append(dominant)

    peak = numeric_summary.get("peak_month", {}).get("mean")
    if peak is not None:
        terms.append(f"mean_peak_month_{peak}")

    for trait_row in common_traits[:3]:
        trait = trait_row.get("trait")
        fraction = safe_float(trait_row.get("fraction"))
        if trait and fraction is not None and fraction >= 0.5:
            terms.append(str(trait))

    # Stable de-duplication
    seen = set()
    unique_terms = []
    for term in terms:
        if term not in seen:
            seen.add(term)
            unique_terms.append(term)

    return unique_terms


def _dominant_value(summary: Optional[Dict[str, Any]]) -> Optional[str]:
    """
    Extract the dominant categorical value from a categorical summary block

    :param summary: Categorical feature summary dictionary, or None if unavailable
    :return: Dominant value as a string, or None when no dominant value is present
    """
    if not summary:
        return None
    dominant = summary.get("dominant")
    return str(dominant) if dominant is not None else None


def save_cluster_summary(cluster_data: dict, file_path: str) -> None:
    """
    Save a human-readable summary of extracted species clusters to a text file

    :param cluster_data: Cluster analysis dictionary
    :param file_path: Output text file path
    """
    clusters = cluster_data.get("clusters", [])

    with open(file_path, "w", encoding="utf-8") as f:
        f.write("\nSpecies clusters")
        f.write("\n================\n")

        for cluster in clusters:
            cluster_id = cluster.get("cluster_id")
            species = cluster.get("species", [])

            f.write(f"\nCluster {cluster_id}\n")
            f.write("-" * (8 + len(str(cluster_id))) + "\n")

            description = cluster.get("description")
            if description:
                f.write(f"{description}\n\n")

            f.write(f"Species ({len(species)}):\n")
            for name in species:
                f.write(f"  {name}\n")

            dominant_family = cluster.get("dominant_model_family")
            dominant_class = cluster.get("dominant_primary_class")

            if dominant_family:
                f.write(f"\nDominant model family : {dominant_family}\n")

            if dominant_class:
                f.write(f"Dominant class        : {dominant_class}\n")

            traits = cluster.get("common_traits", [])

            if traits:
                trait_labels = []

                for item in traits[:5]:
                    if isinstance(item, dict):
                        label = item.get("trait")
                        count = item.get("count")
                        fraction = item.get("fraction")

                        if label is not None and count is not None and fraction is not None:
                            trait_labels.append(f"{label} ({count}, {float(fraction):.0%})")
                        elif label is not None:
                            trait_labels.append(str(label))
                    else:
                        trait_labels.append(str(item))

                f.write(f"Common traits         : {', '.join(trait_labels)}\n")

            numeric = cluster.get("numeric_summary", {})

            peak = numeric.get("peak_month")
            width = numeric.get("season_width_months")

            if peak:
                f.write(f"\nPeak month mean/range : {peak['mean']:.2f} ({peak['min']:.2f} - {peak['max']:.2f})\n")

            if width:
                f.write(f"Season width mean     : {width['mean']:.2f} months\n")

            distinguishing = cluster.get("distinguishing_numeric_features", [])

            if distinguishing:
                f.write("\nDistinguishing numeric features:\n")

                for item in distinguishing[:5]:
                    feature = item.get("feature")
                    direction = item.get("direction")
                    strength = item.get("scaled_difference")

                    if feature is None or direction is None or strength is None:
                        continue

                    f.write(f"  - {feature} ({direction}, scaled_difference={float(strength):.2f})\n")
