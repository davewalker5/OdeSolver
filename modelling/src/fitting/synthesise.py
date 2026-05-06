import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from fitting.io import load_observed_csv, load_and_aggregate_simulated_json


def calculate_scale(observed: pd.Series, simulated: pd.Series, method: str) -> float:
    """
    
    """
    obs = observed.astype(float)
    sim = simulated.astype(float)

    if sim.max() <= 0:
        raise ValueError("Simulated values are all zero; cannot rescale curve.")

    if method == "least_squares":
        denominator = float((sim * sim).sum())
        if denominator == 0:
            raise ValueError("Cannot calculate least-squares scale with zero denominator.")
        return float((obs * sim).sum() / denominator)

    if method == "max":
        return float(obs.max() / sim.max())

    if method == "sum":
        total = float(sim.sum())
        if total == 0:
            raise ValueError("Cannot calculate sum scale with zero simulated total.")
        return float(obs.sum() / total)

    raise ValueError(f"Unsupported scaling method: {method}")


def plot_overlay(result: pd.DataFrame, plot_path: Path, species: str) -> None:
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
    round_values: bool,
) -> pd.DataFrame:
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

