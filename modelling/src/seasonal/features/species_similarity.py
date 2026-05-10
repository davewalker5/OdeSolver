"""
Build pairwise similarity mappings between species from a species feature matrix

The main entry point is:

    build_species_similarity(feature_matrix, output_path)

It accepts the feature matrix dictionary produced by the Stage 1 feature-matrix
builder, writes a JSON similarity artefact, and returns the same artefact as a
Python dictionary for further manipulation
"""

from __future__ import annotations

import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple
from seasonal.support.numeric import clamp


DEFAULT_CIRCULAR_MONTH_FEATURES: Dict[str, float] = {
    # Timing is usually the most ecologically meaningful part of this stage
    "peak_month": 2.0,
    "trough_month": 1.25,
    "season_start_month": 1.25,
    "season_end_month": 1.25,
    "season_midpoint_month": 1.5,
}

DEFAULT_NUMERIC_FEATURES: Dict[str, float] = {
    # Broad shape / magnitude features. These are intentionally conservative:
    # they help distinguish patterns, but should not dominate timing
    "season_width_months": 1.5,
    "target_mean_value": 1.0,
    "target_amplitude": 1.0,
    "baseline_to_peak_ratio": 1.0,
    "autumn_to_winter_weight_ratio": 0.75,
    "year_end_to_winter_weight_ratio": 0.75,
    "decay_to_growth_ratio": 0.75,
    "active_month_count_ge_0_10": 1.0,

    # Fit score is included lightly. A very high/low fit score should not make
    # two species ecologically similar, but it can help flag comparable evidence
    # quality if both values are present
    "fit_score": 0.25,
}

DEFAULT_CATEGORICAL_FEATURES: Dict[str, float] = {
    # model_family is included, but not overwhelmingly. This allows "resident",
    # "seasonal", and "winter" species to remain distinguishable without making
    # cross-family similarity impossible
    "model_family": 1.0,
    "primary_class": 1.0,
    "confidence": 0.25,
    "baseline_presence": 0.75,
    "timing": 1.0,
    "season_width_class": 0.75,
    "window_shape": 0.75,
    "post_peak_decline": 0.75,
    "offseason_suppression": 0.75,
    "summer_suppression": 0.75,
    "autumn_component": 0.75,
    "response_dynamics": 0.75,
}

DEFAULT_COMPONENT_WEIGHTS: Dict[str, float] = {
    "circular_month": 0.40,
    "numeric": 0.25,
    "categorical": 0.20,
    "traits": 0.15,
}


def build_species_similarity(
    feature_matrix: Mapping[str, Any],
    output_path: str | Path,
    top_n: int = 5,
    circular_month_features: Optional[Mapping[str, float]] = None,
    numeric_features: Optional[Mapping[str, float]] = None,
    categorical_features: Optional[Mapping[str, float]] = None,
    component_weights: Optional[Mapping[str, float]] = None,
    include_pairwise: bool = True
) -> Dict[str, Any]:
    """
    Build pairwise and nearest-neighbour species similarity mappings

    :param feature_matrix: Feature matrix dictionary produced by the Stage 1 builder
    :param output_path: Path to the species similarity JSON file
    :param top_n: Number of nearest-neighbour matches to retain for each species
    :param circular_month_features: Mapping of circular month-based feature names to weights
    :param numeric_features: Mapping of linear numeric feature names to weights
    :param categorical_features: Mapping of categorical feature names to weights
    :param component_weights: Mapping controlling the relative contribution of the similarity components
    :param include_pairwise: True to include all mappings, false to include only nearest neighbour
    :return: Species similarity dictionary
    :raises ValueError: If there are errors in the feature matrix
    """

    features = list(feature_matrix.get("features", []))
    if not features:
        raise ValueError("feature_matrix must contain a non-empty 'features' list")

    circular_month_features = dict(circular_month_features or DEFAULT_CIRCULAR_MONTH_FEATURES)
    numeric_features = dict(numeric_features or DEFAULT_NUMERIC_FEATURES)
    categorical_features = dict(categorical_features or DEFAULT_CATEGORICAL_FEATURES)
    component_weights = normalise_weights(dict(component_weights or DEFAULT_COMPONENT_WEIGHTS))

    validate_unique_species(features)

    numeric_ranges = calculate_numeric_ranges(features, numeric_features.keys())

    pairwise: List[Dict[str, Any]] = []
    nearest: Dict[str, List[Dict[str, Any]]] = {str(row["species"]): [] for row in features}

    for i, left in enumerate(features):
        for right in features[i + 1:]:
            comparison = compare_species(
                left,
                right,
                circular_month_features=circular_month_features,
                numeric_features=numeric_features,
                categorical_features=categorical_features,
                component_weights=component_weights,
                numeric_ranges=numeric_ranges,
            )
            pairwise.append(comparison)

            nearest[str(left["species"])].append(neighbour_record(comparison, right))
            nearest[str(right["species"])].append(neighbour_record(comparison, left))

    for species, neighbours in nearest.items():
        neighbours.sort(key=lambda item: item["similarity"], reverse=True)
        nearest[species] = neighbours[:top_n]

    result: Dict[str, Any] = {
        "schema_version": "species-similarity/v1",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "source_feature_schema_version": feature_matrix.get("schema_version"),
        "source_feature_created_utc": feature_matrix.get("created_utc"),
        "n_species": len(features),
        "top_n": top_n,
        "method": {
            "description": (
                "Weighted mixed-feature similarity using circular month distance, "
                "min-max scaled numeric distance, categorical exact-match distance, "
                "and Jaccard trait distance."
            ),
            "distance_range": "0 means identical on compared features; 1 means maximally different",
            "similarity_range": "1 means most similar; 0 means least similar",
            "component_weights": component_weights,
            "circular_month_features": circular_month_features,
            "numeric_features": numeric_features,
            "categorical_features": categorical_features,
            "missing_value_policy": (
                "Missing feature values are skipped for that pair/component. "
                "Component weights are renormalised over available components."
            ),
        },
        "species": [
            {
                "species": row.get("species"),
                "model_family": row.get("model_family"),
                "primary_class": row.get("primary_class"),
            }
            for row in features
        ],
        "nearest_neighbours": nearest,
    }

    if include_pairwise:
        result["pairwise"] = pairwise

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    return result


def compare_species(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    *,
    circular_month_features: Mapping[str, float],
    numeric_features: Mapping[str, float],
    categorical_features: Mapping[str, float],
    component_weights: Mapping[str, float],
    numeric_ranges: Mapping[str, Tuple[float, float]],
) -> Dict[str, Any]:
    """
    Compare two species feature rows and calculate their similarity metrics

    :param left: First species feature row
    :param right: Second species feature row
    :param circular_month_features: Mapping of circular month feature names to weights
    :param numeric_features: Mapping of numeric feature names to weights
    :param categorical_features: Mapping of categorical feature names to weights
    :param component_weights: Mapping controlling the relative contribution of each component
    :param numeric_ranges: Mapping of numeric feature names to their global minimum and maximum values
    :return: Dictionary of similarity information for the two species
    """

    component_distances: Dict[str, Optional[float]] = {
        "circular_month": weighted_circular_month_distance(left, right, circular_month_features),
        "numeric": weighted_numeric_distance(left, right, numeric_features, numeric_ranges),
        "categorical": weighted_categorical_distance(left, right, categorical_features),
        "traits": trait_jaccard_distance(left.get("traits"), right.get("traits")),
    }

    distance = combine_component_distances(component_distances, component_weights)
    similarity = None if distance is None else 1.0 - distance

    return {
        "species_a": left.get("species"),
        "species_b": right.get("species"),
        "model_family_a": left.get("model_family"),
        "model_family_b": right.get("model_family"),
        "primary_class_a": left.get("primary_class"),
        "primary_class_b": right.get("primary_class"),
        "similarity": round_float(similarity),
        "distance": round_float(distance),
        "component_distances": {
            name: round_float(value) for name, value in component_distances.items()
        },
        "compared_feature_counts": {
            "circular_month": count_shared_values(left, right, circular_month_features.keys()),
            "numeric": count_shared_values(left, right, numeric_features.keys()),
            "categorical": count_shared_values(left, right, categorical_features.keys()),
            "traits": count_shared_traits(left.get("traits"), right.get("traits")),
        },
    }


def neighbour_record(comparison: Mapping[str, Any], neighbour: Mapping[str, Any]) -> Dict[str, Any]:
    """
    Create one nearest-neighbour entry from a pairwise comparison

    :param comparison: Pairwise comparison dictionary produced by ``compare_species``
    :param neighbour: Feature-matrix row for the neighbouring species
    :return: Nearest-neighbour record for one species
    """
    return {
        "species": neighbour.get("species"),
        "model_family": neighbour.get("model_family"),
        "primary_class": neighbour.get("primary_class"),
        "similarity": comparison.get("similarity"),
        "distance": comparison.get("distance"),
        "component_distances": comparison.get("component_distances"),
    }


def weighted_circular_month_distance(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    feature_weights: Mapping[str, float],
) -> Optional[float]:
    """
    Calculate the weighted circular month distance between two species records

    :param left: First species feature row to compare
    :param right: Second species feature row to compare
    :param feature_weights: Mapping of circular month feature names to weights
    :return: Weighted average circular month distance scaled from 0.0 to 1.0, or None
    """
    distances: List[Tuple[float, float]] = []

    for feature, weight in feature_weights.items():
        left_value = as_float(left.get(feature))
        right_value = as_float(right.get(feature))
        if left_value is None or right_value is None:
            continue

        distances.append((month_distance(left_value, right_value), float(weight)))

    return weighted_average(distances)


def weighted_numeric_distance(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    feature_weights: Mapping[str, float],
    numeric_ranges: Mapping[str, Tuple[float, float]],
) -> Optional[float]:
    """
    Calculate the weighted numeric distance between two species records

    Numeric values are compared using min-max scaling so that all numeric
    features contribute on a common 0..1 scale regardless of their original
    magnitude

    :param left: First species feature row to compare
    :param right: Second species feature row to compare
    :param feature_weights: Mapping of numeric feature names to weights
    :param numeric_ranges: Mapping of numeric feature names to their global minimum and maximum values
    :return: Weighted average numeric distance scaled from 0.0 to 1.0, or None
    """
    distances: List[Tuple[float, float]] = []

    for feature, weight in feature_weights.items():
        left_value = as_float(left.get(feature))
        right_value = as_float(right.get(feature))
        if left_value is None or right_value is None:
            continue

        minimum, maximum = numeric_ranges.get(feature, (0.0, 0.0))
        value_range = maximum - minimum

        if value_range <= 0:
            distance = 0.0
        else:
            distance = abs(left_value - right_value) / value_range

        distances.append((clamp(distance), float(weight)))

    return weighted_average(distances)


def weighted_categorical_distance(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    feature_weights: Mapping[str, float],
) -> Optional[float]:
    """
    Calculate the weighted categorical distance between two species records

    Matching categories contribute a distance of 0.0 while differing categories
    contribute a distance of 1.0

    :param left: First species feature row to compare
    :param right: Second species feature row to compare
    :param feature_weights: Mapping of categorical feature names to weights
    :return: Weighted average categorical distance scaled from 0.0 to 1.0, or None
    """
    distances: List[Tuple[float, float]] = []

    for feature, weight in feature_weights.items():
        left_value = normalise_category(left.get(feature))
        right_value = normalise_category(right.get(feature))
        if left_value is None or right_value is None:
            continue

        distance = 0.0 if left_value == right_value else 1.0
        distances.append((distance, float(weight)))

    return weighted_average(distances)


def trait_jaccard_distance(left_traits: Any, right_traits: Any) -> Optional[float]:
    """
    Calculate Jaccard distance between two trait collections

    Trait overlap is measured using set intersection and union:

        distance = 1 - (intersection / union)

    :param left_traits: Trait collection for the first species
    :param right_traits: Trait collection for the second species
    :return: Jaccard distance scaled from 0.0 to 1.0, or None
    """
    left_set = set(as_string_list(left_traits))
    right_set = set(as_string_list(right_traits))

    if not left_set and not right_set:
        return None

    union = left_set | right_set
    if not union:
        return None

    intersection = left_set & right_set
    return 1.0 - (len(intersection) / len(union))


def combine_component_distances(
    component_distances: Mapping[str, Optional[float]],
    component_weights: Mapping[str, float],
) -> Optional[float]:
    """
    Combine component distance scores into a single weighted distance

    Components with missing values are skipped and the remaining component
    weights are renormalised through the weighted-average calculation

    :param component_distances: Mapping of component names to distance values
    :param component_weights: Mapping of component names to relative weights
    :return: Combined weighted distance scaled from 0.0 to 1.0, or None
    """
    weighted: List[Tuple[float, float]] = []

    for component, distance in component_distances.items():
        if distance is None:
            continue
        weight = float(component_weights.get(component, 0.0))
        if weight <= 0:
            continue
        weighted.append((distance, weight))

    return weighted_average(weighted)


def month_distance(left_month: float, right_month: float) -> float:
    """
    Calculate circular month distance scaled to the range 0.0..1.0

    Months are treated as positions on a circular calendar so that adjacent
    year-boundary months remain close together

    Examples:
        January vs July => 1.0
        January vs December => 1/6

    :param left_month: First month value
    :param right_month: Second month value
    :return: Circular month distance scaled from 0.0 to 1.0
    """
    diff = abs(left_month - right_month) % 12.0
    circular_diff = min(diff, 12.0 - diff)
    return clamp(circular_diff / 6.0)


def calculate_numeric_ranges(
    features: Sequence[Mapping[str, Any]],
    numeric_feature_names: Iterable[str],
) -> Dict[str, Tuple[float, float]]:
    """
    Calculate global minimum and maximum values for numeric features

    These ranges are later used for min-max scaling during numeric distance
    calculations

    :param features: Sequence of species feature rows
    :param numeric_feature_names: Numeric feature names to analyse
    :return: Mapping of feature names to ``(minimum, maximum)`` tuples
    """
    ranges: Dict[str, Tuple[float, float]] = {}

    for feature in numeric_feature_names:
        values = [
            value
            for row in features
            if (value := as_float(row.get(feature))) is not None
        ]

        if values:
            ranges[feature] = (min(values), max(values))
        else:
            ranges[feature] = (0.0, 0.0)

    return ranges


def validate_unique_species(features: Sequence[Mapping[str, Any]]) -> None:
    """
    Validate that every species row contains a unique species name

    :param features: Sequence of species feature rows
    :raises ValueError: If a species name is missing or duplicated
    """
    seen: set[str] = set()
    duplicates: set[str] = set()

    for row in features:
        species = row.get("species")
        if not species:
            raise ValueError("Every feature row must contain a non-empty 'species' value")

        species_name = str(species)
        if species_name in seen:
            duplicates.add(species_name)
        seen.add(species_name)

    if duplicates:
        names = ", ".join(sorted(duplicates))
        raise ValueError(f"Duplicate species names in feature matrix: {names}")


def count_shared_values(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    feature_names: Iterable[str],
) -> int:
    """
    Count shared non-null feature values between two species rows

    :param left: First species feature row
    :param right: Second species feature row
    :param feature_names: Feature names to test
    :return: Number of features where both rows contain non-null values
    """
    count = 0
    for feature in feature_names:
        if left.get(feature) is not None and right.get(feature) is not None:
            count += 1
    return count


def count_shared_traits(left_traits: Any, right_traits: Any) -> int:
    """
    Count the number of shared traits between two species

    :param left_traits: Trait collection for the first species
    :param right_traits: Trait collection for the second species
    :return: Number of shared traits
    """
    return len(set(as_string_list(left_traits)) & set(as_string_list(right_traits)))


def normalise_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """
    Normalise a weight mapping so the values sum to 1.0

    Non-positive weights are discarded

    :param weights: Raw weight mapping
    :return: Normalised positive-only weight mapping
    :raises ValueError: If no positive weights are present
    """
    total = sum(float(value) for value in weights.values() if float(value) > 0)
    if total <= 0:
        raise ValueError("At least one component weight must be positive")

    return {
        key: float(value) / total
        for key, value in weights.items()
        if float(value) > 0
    }


def weighted_average(values_and_weights: Sequence[Tuple[float, float]]) -> Optional[float]:
    """
    Calculate a weighted average from ``(value, weight)`` pairs

    :param values_and_weights: Sequence of value-weight tuples
    :return: Weighted average value, or None if no valid weights exist
    """
    if not values_and_weights:
        return None

    total_weight = sum(weight for _, weight in values_and_weights)
    if total_weight <= 0:
        return None

    return sum(value * weight for value, weight in values_and_weights) / total_weight


def as_float(value: Any) -> Optional[float]:
    """
    Safely convert a value to a finite float

    Invalid, NaN, or infinite values return None

    :param value: Value to convert
    :return: Finite float value or None
    """
    if value is None:
        return None

    try:
        result = float(value)
    except (TypeError, ValueError):
        return None

    if math.isnan(result) or math.isinf(result):
        return None

    return result


def normalise_category(value: Any) -> Optional[str]:
    """
    Normalise a categorical value into a stripped string

    Empty strings are treated as missing values

    :param value: Category value
    :return: Normalised category string or None
    """
    if value is None:
        return None

    text = str(value).strip()
    return text if text else None


def as_string_list(value: Any) -> List[str]:
    """
    Convert a value into a cleaned list of strings

    Lists and tuples are preserved element-wise while scalar values are wrapped
    into a single-item list

    :param value: Value to convert
    :return: List of non-empty strings
    """
    if value is None:
        return []

    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]

    if isinstance(value, tuple):
        return [str(item) for item in value if str(item).strip()]

    text = str(value).strip()
    return [text] if text else []


def round_float(value: Optional[float], digits: int = 6) -> Optional[float]:
    """
    Round an optional float to a fixed number of decimal places

    :param value: Float value to round
    :param digits: Number of decimal places
    :return: Rounded float or None
    """
    if value is None:
        return None
    return round(float(value), digits)
