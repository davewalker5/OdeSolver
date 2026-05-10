import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from modelling.src.seasonal.support.csv import load_observed_csv
from seasonal.support.json import load_and_aggregate_simulated_json


def calculate_scale(observed: pd.Series, simulated: pd.Series, method: str) -> float:
    """
    Computes a single scaling factor that rescales a simulated curve so that it better
    matches an observed curve

    :param observed: Series of observed values
    :param simulated: Series of simulated values
    :param method: Scaling method
    :return: Scale factor to apply to the simulated data
    """

    # Ensure the series are floating point
    obs = observed.astype(float)
    sim = simulated.astype(float)

    # Check the simulated values can be scaled
    if sim.max() <= 0:
        raise ValueError("Simulated values are all zero; cannot rescale curve.")

    # Find the scale factor that reduces the total squared error between observed and simulated
    if method == "least_squares":
        denominator = float((sim * sim).sum())
        if denominator == 0:
            raise ValueError("Cannot calculate least-squares scale with zero denominator.")
        return float((obs * sim).sum() / denominator)

    # Calculate a scale factor such that the highest simulated point matches the observed peak
    if method == "max":
        return float(obs.max() / sim.max())

    # Calculate a scale factor such that the total area under the curve matches
    if method == "sum":
        total = float(sim.sum())
        if total == 0:
            raise ValueError("Cannot calculate sum scale with zero simulated total.")
        return float(obs.sum() / total)

    raise ValueError(f"Unsupported scaling method: {method}")


def plot_overlay(result: pd.DataFrame, plot_path: Path, species: str) -> None:
    """
    Plot a line chart that overlays scaled simulated and observed values

    :param result: Data frame containing the two series
    :param plot_path: Path to the output file where the chart is exported
    :param species: Species name, for the title
    """
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(result["month"], result["observed"], marker="o", label="Observed")
    ax.plot(result["month"], result["synthesised"], marker="o", label="Synthesised simulation")

    ax.set_title(f"Observed vs Synthesised Simulation: {species.replace('_', ' ').title()}")
    ax.set_xlabel("Month")
    ax.set_ylabel("Value")
    ax.set_xticks(list(range(1, 13)))
    ax.grid(True, which="major", axis="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)


def synthesise(
    species: str,
    observed_path: Path,
    simulated_path: Path,
    output_path: Path,
    plot_path: Path | None,
    scale_method: str,
    aggregation: str,
    round_values: bool
) -> pd.DataFrame:
    """
    Synthesise a curve that follows the shape of the simulated result but scaled to the observed
    data scale

    :param species: Species name
    :param observed_path: Path to the observed data CSV file
    :param simulated_path: Path to the simulated output (JSON)
    :param output_path: Path to the CSV file where the observed and scaled data are written
    :param plot_path: Optional path to the PNG file where the chart is exported
    :param scale_method: Scale method for scaling the simulated data
    :param aggregation: Aggregation method
    :param round_values: Whether or not to round simulated values to integers
    """

    # Load the observed and simulated data and aggregate the latter so there's only one
    # point per month
    observed = load_observed_csv(observed_path)
    simulated = load_and_aggregate_simulated_json(simulated_path, aggregation=aggregation)

    result = observed.merge(simulated, on="month", how="inner")
    scale = calculate_scale(result["observed"], result["simulated_raw"], scale_method)

    result["synthesised"] = result["simulated_raw"] * scale
    if round_values:
        result["synthesised"] = result["synthesised"].round().astype(int)

    result.attrs["scale"] = scale
    result.attrs["scale_method"] = scale_method
    result.attrs["aggregation"] = aggregation

    result.to_csv(output_path, index=False)

    if plot_path is not None:
        plot_overlay(result, plot_path, species)
