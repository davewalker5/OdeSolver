
from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

import numpy as np
import re
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform


def build_distance_matrix(similarity_matrix: np.ndarray) -> np.ndarray:
    """
    Turn the similarity matrix into a distance matrix where the diagonal, where a
    species is compared to itself, is scored 0.0. Distance is calculated as 1.0 -
    similarity

    :param similarity_matrix: The species similarity matrix
    :return: The distance matrix calculated from the similarity scores
    """
    distance_matrix = 1.0 - similarity_matrix
    np.fill_diagonal(distance_matrix, 0.0)
    return distance_matrix


def build_linkage_matrix(similarity_matrix: np.ndarray, linkage_method: str = "average") -> np.ndarray:
    """
    Convert a similarity matrix to a distance matrix, convert to SciPy's condensed form and
    perform hierarchical agglomerative clustering: each species starts as its own cluster,
    then the closest clusters are repeatedly merged. The return from linkage is the merge
    history essentially as a dendrogram

    :param similarity_matrix: The species similarity matrix
    :param linkage_method: Merge method
    :return: The hierarchical merge dendrogram
    """
    distance_matrix = build_distance_matrix(similarity_matrix)
    condensed = squareform(distance_matrix, checks=False)
    return linkage(condensed, method=linkage_method)


def order_species_by_linkage(similarity_matrix: np.ndarray, linkage_method: str = "average") -> Tuple[List[int], np.ndarray]:
    """
    Perform hierarchical agglomerative clustering on the similarity data and order species
    by leaf order in the dendrogram, which places similar species closer together

    :param similarity_matrix: The species similarity matrix
    :param linkage_method: Merge method
    :return: Tuple of a list of leaf node IDs and the hierarchical merge dendrogram
    """
    linkage_matrix = build_linkage_matrix(similarity_matrix, linkage_method=linkage_method)
    order = leaves_list(linkage_matrix).tolist()
    return order, linkage_matrix


def serialise_linkage_matrix(
    linkage_matrix: np.ndarray,
    species_names: Sequence[str],
    leaf_order: Sequence[int] | None = None,
    *,
    decimals: int = 6,
) -> Dict[str, Any]:
    """
    Convert a SciPy linkage matrix into a JSON-friendly dendrogram description.

    SciPy linkage rows use integer node IDs: original observations are leaves
    0..n-1, and newly merged internal nodes are n..2n-2 in row order. This
    function preserves that convention so the JSON can be converted back to a
    SciPy linkage matrix for plotting, while also adding species names and child
    membership lists for easier inspection.

    :param linkage_matrix: SciPy linkage matrix with columns child_1, child_2,
        distance and n_leaves
    :param species_names: Species names in the same order used to build the
        similarity matrix
    :param leaf_order: Optional dendrogram leaf order returned by leaves_list
    :param decimals: Number of decimal places used for stored distances
    :return: JSON-serialisable linkage metadata and merge details
    """
    n_species = len(species_names)
    if linkage_matrix.shape != (max(n_species - 1, 0), 4):
        raise ValueError(
            "linkage_matrix shape does not match species_names length: "
            f"shape={linkage_matrix.shape}, n_species={n_species}"
        )

    species_by_node_id: Dict[int, List[str]] = {
        i: [str(name)] for i, name in enumerate(species_names)
    }

    merges: List[Dict[str, Any]] = []
    scipy_rows: List[List[float]] = []

    for row_index, row in enumerate(linkage_matrix):
        left_id = int(row[0])
        right_id = int(row[1])
        distance = round(float(row[2]), decimals)
        n_leaves = int(row[3])
        node_id = n_species + row_index

        left_species = species_by_node_id[left_id]
        right_species = species_by_node_id[right_id]
        merged_species = left_species + right_species
        species_by_node_id[node_id] = merged_species

        scipy_rows.append([left_id, right_id, distance, n_leaves])
        merges.append(
            {
                "node_id": node_id,
                "left_child": left_id,
                "right_child": right_id,
                "distance": distance,
                "n_leaves": n_leaves,
                "species": merged_species,
                "left_species": left_species,
                "right_species": right_species,
            }
        )

    return {
        "format": "scipy.cluster.hierarchy.linkage",
        "columns": ["left_child", "right_child", "distance", "n_leaves"],
        "node_id_convention": (
            "Leaf nodes are 0..n_species-1 in species_input_order; internal nodes "
            "are n_species..2*n_species-2 in linkage row order."
        ),
        "species_input_order": list(species_names),
        "leaf_order_indices": list(leaf_order) if leaf_order is not None else None,
        "leaf_order_species": (
            [str(species_names[i]) for i in leaf_order] if leaf_order is not None else None
        ),
        "matrix": scipy_rows,
        "merges": merges,
    }


def first_sentence(text: str) -> str:
    """
    Extract the first sentence, excluding trainling full-stop, from a cluster description

    :param text: Full text
    :return: First sentence of the text
    """
    if not text:
        return ""

    match = re.search(r"(?<=[.!?])\s+", text.strip())
    return text.strip() if not match else text[: match.start()].strip().removesuffix(".")
