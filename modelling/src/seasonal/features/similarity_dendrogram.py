from pathlib import Path
from typing import Any, Dict
import re

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import to_hex
from matplotlib.patches import Patch
from scipy.cluster.hierarchy import dendrogram


def _first_sentence(text: str) -> str:
    """
    Extract the first sentence, excluding trainling full-stop, from a cluster description
    
    :param text: Full text
    :return: First sentence of the text
    """
    if not text:
        return ""
    match = re.search(r"(?<=[.!?])\s+", text.strip())
    return text.strip() if not match else text[: match.start()].strip()


def _get_cluster_colour(
        node_id: int,
        colour_clusters: bool,
        species_cluster_ids: Any,
        species_names: list,
        node_to_leaves: dict,
        cluster_colours: dict
) -> str:
    """
    Given a SciPy node ID, determine the colour for that branch of the dendogram based
    on the leaf nodes under it

    :param node_id: SciPy node ID
    :param colour_clusters: True to colour clusters, else use black
    :param species_cluster_ids: Dictionary of cluster ID membership by species
    :param species_names: List of species names
    :param node_to_leaves: Lookup from each SciPy node id to the leaf nodes under it
    :param cluster_colours: Dictionary of cluster colours by cluster ID
    """
    if not colour_clusters:
        return "black"

    leaf_clusters = {
        species_cluster_ids.get(species_names[i])
        for i in node_to_leaves[int(node_id)]
    }

    leaf_clusters.discard(None)

    if len(leaf_clusters) == 1:
        cluster_id = next(iter(leaf_clusters))
        return cluster_colours.get(cluster_id, "black")

    return "black"


def plot_species_cluster_dendrogram(
    cluster_data: Dict[str, Any],
    output_png_path: str | Path,
    figsize: tuple[float, float] | None = None,
    dpi: int = 180,
    title: str = "Species Similarity Dendrogram",
    colour_clusters: bool = True
) -> None:
    
    # Load the data and extract the species and cluster details
    linkage_info = cluster_data.get("linkage", {})
    linkage_matrix = np.asarray(linkage_info.get("matrix"), dtype=float)
    species_names = list(linkage_info.get("species_input_order", []))
    species_cluster_ids = cluster_data.get("species_cluster_ids", {})

    if linkage_matrix.ndim != 2 or linkage_matrix.shape[1] != 4:
        raise ValueError("cluster_data['linkage']['matrix'] must be an n x 4 linkage matrix")

    if linkage_matrix.shape[0] != len(species_names) - 1:
        raise ValueError("Linkage matrix row count does not match species count")

    labels = [
        f"{species} [{species_cluster_ids.get(species, '?')}]"
        for species in species_names
    ]

    cluster_ids = sorted(
        {cluster_id for cluster_id in species_cluster_ids.values() if cluster_id is not None}
    )
    cmap = plt.get_cmap("tab20")
    cluster_colours = {
        cluster_id: to_hex(cmap(i % cmap.N))
        for i, cluster_id in enumerate(cluster_ids)
    }

    # Build a lookup from each SciPy node id to the leaf indices under it.
    # Leaves are 0..n_species-1; internal nodes are n_species..2*n_species-2.
    n_species = len(species_names)
    node_to_leaves: dict[int, set[int]] = {
        i: {i}
        for i in range(n_species)
    }
    for row_index, row in enumerate(linkage_matrix):
        node_id = n_species + row_index
        left_child = int(row[0])
        right_child = int(row[1])
        node_to_leaves[node_id] = (
            node_to_leaves[left_child] | node_to_leaves[right_child]
        )

    if figsize is None:
        figsize = (12, max(7, len(species_names) * 0.32))

    output_png_path = Path(output_png_path)
    output_png_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=figsize)

    def link_colour_func(node_id: int) -> str:
        return _get_cluster_colour(node_id, colour_clusters, species_cluster_ids, species_names,
                                   node_to_leaves, cluster_colours)

    dendro = dendrogram(
        linkage_matrix,
        labels=labels,
        orientation="left",
        leaf_font_size=8,
        color_threshold=None,
        link_color_func=link_colour_func,
        above_threshold_color="black",
        ax=ax,
    )

    ax.set_title(title)
    ax.set_xlabel("Distance: 1 - similarity")
    ax.set_ylabel("Species")
    ax.grid(axis="x", alpha=0.25)

    # ------------------------------------------------------------
    # Cluster span markers on the left of the plot
    # ------------------------------------------------------------
    leaf_indices = dendro["leaves"]

    plotted_species = [species_names[i] for i in leaf_indices]
    plotted_cluster_ids = [
        species_cluster_ids.get(species)
        for species in plotted_species
    ]

    # SciPy places leaves at y = 5, 15, 25, ...
    y_positions = {
        species: 5 + i * 10
        for i, species in enumerate(plotted_species)
    }

    cluster_to_species: dict[int, list[str]] = {}
    for species, cluster_id in zip(plotted_species, plotted_cluster_ids):
        if cluster_id is None:
            continue
        cluster_to_species.setdefault(cluster_id, []).append(species)

    # x is in axes coordinates; y is in data coordinates.
    # Negative x puts the markers into the left margin.
    transform = ax.get_yaxis_transform()

    marker_x = -0.05
    cap_half_width = 0.018
    label_gap = 4.5

    for cluster_id in sorted(cluster_to_species):
        cluster_colour = cluster_colours.get(cluster_id, "black")
        ys = [y_positions[species] for species in cluster_to_species[cluster_id]]
        y_min = min(ys) - 4
        y_max = max(ys) + 4
        y_mid = (y_min + y_max) / 2

        # Split the vertical span so the number sits in the gap.
        ax.plot(
            [marker_x, marker_x],
            [y_min, y_mid - label_gap],
            transform=transform,
            clip_on=False,
            linewidth=1.2,
            color=cluster_colour,
        )
        ax.plot(
            [marker_x, marker_x],
            [y_mid + label_gap, y_max],
            transform=transform,
            clip_on=False,
            linewidth=1.2,
            color=cluster_colour,
        )

        # Caps at top and bottom of the span.
        ax.plot(
            [marker_x - cap_half_width, marker_x + cap_half_width],
            [y_min, y_min],
            transform=transform,
            clip_on=False,
            linewidth=1.2,
            color=cluster_colour,
        )
        ax.plot(
            [marker_x - cap_half_width, marker_x + cap_half_width],
            [y_max, y_max],
            transform=transform,
            clip_on=False,
            linewidth=1.2,
            color=cluster_colour,
        )

        ax.text(
            marker_x,
            y_mid,
            str(cluster_id),
            transform=transform,
            ha="center",
            va="center",
            fontsize=9,
            fontweight="bold",
            color=cluster_colour,
            clip_on=False,
        )

    # ------------------------------------------------------------
    # Legend below the chart
    # ------------------------------------------------------------

    # Get the descriptions for all the clusters
    cluster_descriptions = {
        c["cluster_id"]: _first_sentence(c.get("description", ""))
        for c in cluster_data.get("clusters", [])
    }

    # Build the legend handles
    legend_handles = []
    for cluster_id in sorted(cluster_to_species):
        description = f"{cluster_id} : {cluster_descriptions.get(cluster_id, '')}"
        legend_handles.append(Patch(facecolor=cluster_colours[cluster_id], label=description))

    ax.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.08),
        fontsize=8,
        title_fontsize=8,
        frameon=False,
        ncol=1,
    )

    # Leave room on the left for cluster bars
    fig.subplots_adjust(left=0.2, bottom=0.32)

    fig.savefig(output_png_path, dpi=dpi, bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
