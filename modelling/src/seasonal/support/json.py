import json
import pandas as pd
from decimal import Decimal
from pathlib import Path
from typing import Any
from seasonal.support.numeric import D


def coerce_json_value(value: Any) -> Any:
    """
    Convert values into JSON-friendly scalar representations

    :param value: Value that may include ``Decimal`` or other non-JSON-native types
    :return: JSON-friendly value suitable for inclusion in the classification output
    """
    if isinstance(value, Decimal):
        return float(value)
    try:
        Decimal(str(value))
        return float(value)
    except Exception:
        return value


def load_json(path: Path) -> dict[str, Any]:
    """
    Load a JSON file and return a dictionary of its contents

    :param path: Path to the file to load
    :return: Dictionary of JSON contents
    """
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def write_json(path: Path, content: dict[str, Any], indent: int = 2) -> None:
    """
    Write a dictionary to a JSON file

    :param path: Path to the file to save
    :param content: Dictionary to save
    :param ident: JSON indentation level
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(content, f, indent=indent, ensure_ascii=False)
        f.write("\n")


def load_simulated_json(path: str) -> list:
    """
    Load JSON simulation output from the ODE Solver.

    :param path: Path to simulation output file
    :return: List of dictionaries, each containing t and y
    """
    data = load_json(path)
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
