
from __future__ import annotations

from typing import List, Tuple

import numpy as np
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
