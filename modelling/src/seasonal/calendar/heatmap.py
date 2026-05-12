from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
               "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def plot_neighbourhood_calendar_heatmap(
    calendar_activity: dict[str, Any],
    output_path: str | Path,
    title: str = "Seasonal Ecological Calendar",
) -> None:
    """
    Plot an analytical neighbourhood x month heatmap from a seasonal ecological
    calendar activity artefact

    :param calendar_activity: Neighbourhood calendar activity dictionary
    :param output_path: Path to the output activity JSON file to create
    """

    from matplotlib.gridspec import GridSpec

    clusters = calendar_activity.get("clusters", [])

    if not clusters:
        raise ValueError("calendar_activity contains no clusters")

    labels: list[str] = []
    matrix: list[list[float]] = []

    for cluster in clusters:
        cluster_id = cluster.get("cluster_id")
        # labels.append(f"Cluster {cluster_id}")
        labels.append(cluster_id)

        month_values = [0.0] * 12

        for item in cluster.get("monthly_activity", []):
            month = int(item["month"])
            if 1 <= month <= 12:
                month_values[month - 1] = float(
                    item.get("mean_activity", 0.0)
                )

        matrix.append(month_values)

    data = np.array(matrix)

    fig_height = max(5.5, 0.55 * len(labels) + 2.2)

    fig = plt.figure(figsize=(14, fig_height))

    gs = GridSpec(
        2,
        1,
        height_ratios=[4, 1.35],
        hspace=0.22,
        figure=fig,
    )

    ax = fig.add_subplot(gs[0])
    legend_ax = fig.add_subplot(gs[1])

    im = ax.imshow(
        data,
        aspect="auto",
        vmin=0,
        vmax=1,
        cmap="YlOrRd"
    )

    ax.set_xticks(range(12))
    ax.set_xticklabels(MONTH_NAMES)

    ax.set_yticks(range(len(labels)))
    ax.set_yticklabels(labels)

    ax.set_xlabel("Month")
    ax.set_ylabel("Cluster")
    ax.set_title(title)

    cbar = fig.colorbar(
        im,
        ax=ax,
        fraction=0.035,
        pad=0.035,
    )
    cbar.set_label("Mean normalised activity")

    legend_ax.axis("off")

    legend_lines = ["Cluster Descriptions:", "\n"]

    for cluster in clusters:
        cluster_id = cluster.get("cluster_id")
        label = cluster.get("calendar_label", cluster_id)
        legend_lines.append(f"{cluster_id}: {label}")

    legend_text = "\n".join(legend_lines)

    legend_ax.text(
        0.0,
        1.0,
        legend_text,
        fontsize=10,
        va="top",
        ha="left",
        transform=legend_ax.transAxes,
    )

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        output_path,
        dpi=200,
        bbox_inches="tight",
    )

    plt.close(fig)
