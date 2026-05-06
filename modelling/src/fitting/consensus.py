import csv
import json
from decimal import Decimal
from pathlib import Path
from statistics import median
from fitting.utils import D, format_decimal


def load_rows(path):
    """
    Load a parameters CSV file
    """
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def consensus(rows, parameters):
    """
    Calculate consensus parameters from a set of rows containing one parameter set per row

    :param rows: Collection of parameter sets
    :param parameters: Parameters to include in the consensus set
    """
    result = {}

    param_names = [p for p in parameters if p not in ["TIMESTAMP", "OBSERVED"]]
    for param in param_names:
        values = [D(row[param]) for row in rows if row.get(param) not in ("", None)]

        if not values:
            continue

        result[param] = format_decimal(median(values))

    return result


def write_consensus_parameters(
        input: str,
        output: str,
        species: str,
        parameters: list,
        top_percent: Decimal = D("20")) -> None:

    """
    Generate consensus parametes from a CSV file containing parameters, one set per row, from a
    parameter fitting run

    :param input: Input CSV file path
    :param output: Output parameters JSON path
    :param top_percent: % of runs to keep
    :param parameters: List of parameter names to include in the consensus
    """

    # Load the parameters CSV file
    rows = load_rows(input)
    if not rows:
        raise ValueError("Input CSV contains no rows")

    # Make sure the scoring field is there
    if "SCORE" not in rows[0]:
        raise ValueError("Input CSV must contain a SCORE column")

    # Sort by score, calculate the number of rows to keep and identify the best rows
    rows = sorted(rows, key=lambda r: D(r["SCORE"]))
    keep_count = max(1, int(len(rows) * (top_percent / Decimal("100"))))
    best_rows = rows[:keep_count]

    # Calculate consensus parameters and write the consensus file
    params = consensus(best_rows, parameters)
    params["SPECIES"] = species.replace("_", " ").title()
    Path(output).write_text(json.dumps(params, indent=2) + "\n")
