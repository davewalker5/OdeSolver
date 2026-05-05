"""
Create a monthly synthesised data series that keeps the shape of a simulated
ODE curve but rescales it onto the observed data scale.

Example:
    python synthesise_simulated_curve.py \
        brimstone_butterfly_observed.csv \
        brimstone_butterfly_simulated.csv \
        -o brimstone_butterfly_synthesised.csv \
        -p brimstone_butterfly_overlay.png
"""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


MONTHS = list(range(1, 13))


def read_observed(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)

    required = {"month", "value"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Observed CSV is missing required columns: {sorted(missing)}")

    out = df[["month", "value"]].copy()
    out["month"] = out["month"].astype(int)
    out["observed"] = pd.to_numeric(out["value"], errors="raise")
    out = out[["month", "observed"]]

    # Ensure all months are present, filling absent months as zero.
    return (
        pd.DataFrame({"month": MONTHS})
        .merge(out, on="month", how="left")
        .fillna({"observed": 0})
    )


def read_simulated_monthly(path: Path, aggregation: str = "mean") -> pd.DataFrame:
    df = pd.read_csv(path)

    required = {"t", "y"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Simulated CSV is missing required columns: {sorted(missing)}")

    sim = df[["t", "y"]].copy()
    sim["t"] = pd.to_numeric(sim["t"], errors="raise")
    sim["y"] = pd.to_numeric(sim["y"], errors="raise")

    # Treat t as months since start of year.
    # Month 1 = 0.0 <= t < 1.0, Month 2 = 1.0 <= t < 2.0, etc.
    # Drop t >= 12 because that belongs to the next cycle/year.
    sim = sim[(sim["t"] >= 0) & (sim["t"] < 12)].copy()
    sim["month"] = sim["t"].astype(int) + 1

    if aggregation == "mean":
        monthly = sim.groupby("month", as_index=False)["y"].mean()
    elif aggregation == "max":
        monthly = sim.groupby("month", as_index=False)["y"].max()
    elif aggregation == "last":
        monthly = sim.sort_values("t").groupby("month", as_index=False)["y"].last()
    else:
        raise ValueError(f"Unsupported aggregation: {aggregation}")

    monthly = monthly.rename(columns={"y": "simulated_raw"})

    return (
        pd.DataFrame({"month": MONTHS})
        .merge(monthly, on="month", how="left")
        .fillna({"simulated_raw": 0})
    )


def calculate_scale(observed: pd.Series, simulated: pd.Series, method: str) -> float:
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


def synthesise(
    observed_path: Path,
    simulated_path: Path,
    output_path: Path,
    plot_path: Path | None,
    scale_method: str,
    aggregation: str,
    round_values: bool,
) -> pd.DataFrame:
    observed = read_observed(observed_path)
    simulated = read_simulated_monthly(simulated_path, aggregation=aggregation)

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
        plot_overlay(result, plot_path, observed_path.stem.replace("_observed", ""))

    return result


def plot_overlay(result: pd.DataFrame, plot_path: Path, title_species: str) -> None:
    fig, ax = plt.subplots(figsize=(9, 5))

    ax.plot(result["month"], result["observed"], marker="o", label="Observed")
    ax.plot(result["month"], result["synthesised"], marker="o", label="Synthesised simulation")

    ax.set_title(f"Observed vs synthesised simulation: {title_species.replace('_', ' ')}")
    ax.set_xlabel("Month")
    ax.set_ylabel("Value")
    ax.set_xticks(MONTHS)
    ax.grid(True, which="major", axis="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(plot_path, dpi=150)
    plt.close(fig)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("-ob", "--observed", type=Path, help="CSV with month,value columns")
    parser.add_argument("-si", "--simulated", type=Path, help="Solver CSV with t,y columns")
    parser.add_argument("-o", "--output-csv", type=Path, help="Output CSV path. Default: <species>_synthesised.csv")
    parser.add_argument("-p", "--plot", type=Path, help="Optional output plot path, e.g. <species>_synthesised.png")
    parser.add_argument("-sm", "--scale-method", choices=["least_squares", "max", "sum"], default="least_squares", help="How to rescale the simulated shape onto the observed scale")
    parser.add_argument("-a", "--aggregation", choices=["mean", "max", "last"], default="mean", help="How to convert the solver's sub-monthly output into monthly values")
    parser.add_argument("-r", "--round", action="store_true", help="Round synthesised values to integer counts")
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    if args.output_csv is None:
        species = args.observed_csv.stem.replace("_observed", "")
        args.output_csv = args.observed_csv.with_name(f"{species}_synthesised.csv")

    result = synthesise(
        args.observed,
        args.simulated,
        args.output_csv,
        args.plot,
        args.scale_method,
        args.aggregation,
        args.round)

    print(f"Wrote: {args.output_csv}")
    if args.plot:
        print(f"Wrote: {args.plot}")
    print(f"Scale method: {result.attrs['scale_method']}")
    print(f"Monthly aggregation: {result.attrs['aggregation']}")
    print(f"Scale factor: {result.attrs['scale']:.6g}")


if __name__ == "__main__":
    main()
