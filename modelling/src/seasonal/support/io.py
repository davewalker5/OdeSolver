import os
import csv
import json
import pandas as pd
from pathlib import Path
from seasonal.support.utils import D


def append_params_to_csv(params: dict, colums: list, csv_path: str) -> None:
    """
    Append fitted parameters to a CSV file, one row per run.

    :param params: Fitted simulation parameters
    :param csv_path: CSV file to write to
    """
    file_exists = os.path.exists(csv_path)

    with open(csv_path, mode="a", newline="") as f:
        writer = csv.writer(f)

        if not file_exists:
            writer.writerow(colums)

        writer.writerow([params.get(col, "") for col in colums])


def load_observed_csv(csv_path: Path) -> pd.DataFrame:
    """
    Load the observed data and make sure all months are represented, padding with zeros

    :param csv_path: CSV file path
    :return: Set of monthly values
    """
    df = pd.read_csv(csv_path)

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
        pd.DataFrame({"month": list(range(1, 13))})
        .merge(out, on="month", how="left")
        .fillna({"observed": 0})
    )


def load_and_normalise_observed_csv(path: str) -> dict:
    """
    Load the observed data and normalise it into the range 0..1

    The CSV file is expected to contain:

    - month: month number, 1..12
    - value: observed presence/detectability/count value

    :param path: Path to observed CSV
    :return: Normalised observed data keyed by month
    """
    rows = {}

    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            month = int(row["month"])
            value = D(row["value"])
            rows[month] = value

    max_value = max(rows.values())

    if max_value == 0:
        return {m: D("0") for m in rows}

    return {month: value / max_value for month, value in rows.items()}


def load_simulated_json(path: str) -> list:
    """
    Load JSON simulation output from the ODE Solver.

    :param path: Path to simulation output file
    :return: List of dictionaries, each containing t and y
    """
    with open(path) as f:
        data = json.load(f)

    points = []

    for p in data:
        y_key = "y_normalised" if "y_normalised" in p else "y"
        points.append({"t": D(p["t"]), "y": D(p[y_key])})

    return points


def load_and_aggregate_simulated_json(path: Path, aggregation: str = "mean") -> pd.DataFrame:
    """
    Load the simulated data, aggregating by month
    
    :param path: Path to the simulated CSV file
    :param aggregation: Aggregation method
    """
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
        pd.DataFrame({"month": list(range(1, 13))})
        .merge(monthly, on="month", how="left")
        .fillna({"simulated_raw": 0})
    )
