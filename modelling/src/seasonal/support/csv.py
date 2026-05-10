import os
import csv
import pandas as pd
from pathlib import Path
from seasonal.support.numeric import D


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
