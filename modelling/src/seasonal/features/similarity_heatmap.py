from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
from seasonal.features.clustering import order_species_by_linkage
from seasonal.features.species_similarity import build_similarity_matrix, extract_species_names


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
    species_names = extract_species_names(similarity_data)
    matrix = build_similarity_matrix(species_names, similarity_data)

    if cluster:
        order, _ = order_species_by_linkage(matrix, linkage_method="average")
    else:
        order = list(range(matrix.shape[0]))

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
