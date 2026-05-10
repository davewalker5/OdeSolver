from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple
import matplotlib.pyplot as plt
import numpy as np
from scipy.cluster.hierarchy import leaves_list, linkage
from scipy.spatial.distance import squareform


def generate_species_similarity_heatmap(
    similarity_data: Dict[str, Any],
    output_path: str | Path,
    title: str = "Species similarity heatmap",
    cluster: bool = True,
    figsize: Optional[Tuple[float, float]] = None,
    dpi: int = 200,
    show_values: bool = True,
    value_font_size: int = 5,
    label_font_size: int = 7,
) -> Dict[str, Any]:
    """
    Generate a PNG heatmap from species similarity data

    :param similarity_data: Species similarity data
    :param output_path: Path to the output PNG file
    :param title: Chart title
    :param cluster: Cluster the data so similar species are placed near one another
    :param figsize: Matplotlib figure size
    :param dpi: Generated image resolution
    :param show_values: True to write numeric similarity values into each heatmap cell
    :param value_font_size: Font size used to write values into the cells
    :param label_font_size: Font size used for species labels
    """

    # Extract the species names and generate the 2D heatmap matrix
    species_names = _extract_species_names(similarity_data)
    matrix = _build_similarity_matrix(species_names, similarity_data)

    order = _order_species(matrix, cluster)
    ordered_names = [species_names[i] for i in order]
    ordered_matrix = matrix[np.ix_(order, order)]

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if figsize is None:
        figsize = _default_figsize(len(species_names))

    fig, ax = plt.subplots(figsize=figsize)

    image = ax.imshow(
        ordered_matrix,
        vmin=0.0,
        vmax=1.0,
        interpolation="nearest",
        aspect="equal",
        cmap="YlOrRd"
    )

    ax.set_title(title, pad=16)
    ax.set_xticks(np.arange(len(ordered_names)))
    ax.set_yticks(np.arange(len(ordered_names)))
    ax.set_xticklabels(ordered_names, rotation=90, fontsize=label_font_size)
    ax.set_yticklabels(ordered_names, fontsize=label_font_size)

    ax.set_xlabel("Species")
    ax.set_ylabel("Species")

    # Thin gridlines improve readability without turning the figure into a table.
    ax.set_xticks(np.arange(-0.5, len(ordered_names), 1), minor=True)
    ax.set_yticks(np.arange(-0.5, len(ordered_names), 1), minor=True)
    ax.grid(which="minor", linewidth=0.25)
    ax.tick_params(which="minor", bottom=False, left=False)

    if show_values:
        _annotate_values(ax, ordered_matrix, font_size=value_font_size)

    cbar = fig.colorbar(image, ax=ax, fraction=0.046, pad=0.04)
    cbar.set_label("Similarity")

    fig.tight_layout()
    fig.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)


def _extract_species_names(similarity_data: Dict[str, Any]) -> List[str]:
    """
    Extract a list of species names from the similarity data

    :param similarity_data: Species similarity data
    :return: A list of species names
    """
    # Extract the species entries from the similarity data
    species_entries = similarity_data.get("species")
    if not isinstance(species_entries, list) or not species_entries:
        raise ValueError("similarity_data must contain a non-empty 'species' list")

    # Extract the species names from the entries
    names: List[str] = []
    for entry in species_entries:
        if not isinstance(entry, dict) or not entry.get("species"):
            raise ValueError("Each species entry must be a dictionary with a 'species' value")
        names.append(str(entry["species"]))

    if len(set(names)) != len(names):
        raise ValueError("Species names must be unique")

    return names


def _build_similarity_matrix(species_names: Sequence[str], similarity_data: Dict[str, Any]) -> np.ndarray:
    """
    Convert the similarity data into a 2D matrix that the heatmap can render. If the original data looks like this:

    [
        {
            "species_a": "Robin",
            "species_b": "Blackbird",
            "similarity": 0.81
        },
        ...
    ]

    the matrix looks like this:

                Robin   Blackbird   Swift
    Robin       1.0     0.81        0.14
    Blackbird   0.81    1.0         0.11
    Swift       0.14    0.11        1.0
    
    :param species_names: Ordered list of species names
    :param similarity_data: Species similarity data
    :return: Similarity matrix
    """
    pairwise = similarity_data.get("pairwise")

    if not isinstance(pairwise, list):
        raise ValueError("similarity_data must contain a 'pairwise' list")

    name_to_index = {name: i for i, name in enumerate(species_names)}
    n_species = len(species_names)

    matrix = np.full((n_species, n_species), np.nan, dtype=float)
    np.fill_diagonal(matrix, 1.0)

    for record in pairwise:
        if not isinstance(record, dict):
            continue

        species_a = record.get("species_a")
        species_b = record.get("species_b")
        similarity = record.get("similarity")

        if species_a not in name_to_index or species_b not in name_to_index:
            continue

        if similarity is None:
            continue

        try:
            similarity_value = float(similarity)
        except (TypeError, ValueError):
            continue

        i = name_to_index[species_a]
        j = name_to_index[species_b]

        matrix[i, j] = similarity_value
        matrix[j, i] = similarity_value

    if np.isnan(matrix).any():
        missing = int(np.isnan(matrix).sum())
        raise ValueError(f"Similarity matrix is incomplete: {missing} missing cells")

    return matrix


def _order_species(matrix: np.ndarray, cluster: bool) -> List[int]:
    """
    Re-order the matrix so similar species sit close to one another. This is what turns the heatmap
    into something visually meaningful rather than just a giant noisy square! :)
    
    :param matrix: Similarity matrix
    :param cluster: True to use SciPy clustering
    :return: Re-ordered list of matrix indices
    """
    if not cluster:
        return list(range(matrix.shape[0]))

    # Convert similarity to distance in which a similarity of 1.0 becomes a distance of 0.0
    distance_matrix = 1.0 - matrix
    np.fill_diagonal(distance_matrix, 0.0)

    # Convert to condensed distance form and generate a dendogram (internally). leaves_list() then
    # gives the left-to-right or top-to-bottom ordering of species (indices)
    condensed = squareform(distance_matrix, checks=False)
    linkage_matrix = linkage(condensed, method="average")
    order = leaves_list(linkage_matrix).tolist()

    return order


def _default_figsize(n_species: int) -> Tuple[float, float]:
    """
    Calculate a default figure size that's large enough for readable labels

    :param n_species: Number of species
    :return: Tuple of the width and height of the figure
    """
    side = max(8.0, min(18.0, n_species * 0.32))
    return side, side


def _annotate_values(ax: Any, matrix: np.ndarray, *, font_size: int) -> None:
    """
    Write similarity values into each cell in the heatmap

    :param ax:
    :param matrix:
    :param font_size:
    """
    n_rows, n_cols = matrix.shape

    for row in range(n_rows):
        for col in range(n_cols):
            value = matrix[row, col]
            text_colour = "white" if value >= 0.8 else "black"
            ax.text(
                col,
                row,
                f"{value:.2f}",
                ha="center",
                va="center",
                fontsize=font_size,
                color=text_colour
            )
