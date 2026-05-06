import argparse
import csv
import json
from decimal import Decimal
from pathlib import Path
from statistics import median


PARAMETERS = [
    "GROWTH",
    "DECAY",
    "OOS_DECAY",
    "POST_PEAK_DECAY",
    "POST_PEAK_SHARPNESS",
    "DECAY_POWER",
    "SEASON_START",
    "SEASON_END",
    "SHARPNESS",
    "FORCING_PEAK"
]


def D(value):
    return Decimal(str(value))


def load_rows(path):
    with open(path, newline="") as f:
        return list(csv.DictReader(f))


def format_decimal(value, places=3):
    value = D(value).quantize(Decimal("1." + "0" * places))
    return str(value.normalize())


def consensus(rows):
    result = {}

    for param in PARAMETERS:
        values = [D(row[param]) for row in rows if row.get(param) not in ("", None)]

        if not values:
            continue

        result[param] = format_decimal(median(values))

    return result


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("-i", "--input", required=True, help="Input parameters CSV")
    parser.add_argument("-o", "--output", required=True, help="Output parameters JSON")
    parser.add_argument("-s", "--species", required=True, help="Species name")
    parser.add_argument("-tp", "--top-percent", type=Decimal, default=Decimal("20"), help="Top percentage of rows to use, sorted by SCORE. Default: 20")
    args = parser.parse_args()

    # Load the parameters CSV file
    rows = load_rows(args.input)
    if not rows:
        raise ValueError("Input CSV contains no rows")

    # Make sure the scoring field is there
    if "SCORE" not in rows[0]:
        raise ValueError("Input CSV must contain a SCORE column")

    # Sort by score, calculate the number of rows to keep and identify the best rows
    rows = sorted(rows, key=lambda r: D(r["SCORE"]))
    keep_count = max(1, int(len(rows) * (args.top_percent / Decimal("100"))))
    best_rows = rows[:keep_count]

    # Calculate consensus parameters and write the consensus file
    params = consensus(best_rows)
    params["SPECIES"] = args.species.replace("_", " ").title()
    Path(args.output).write_text(json.dumps(params, indent=2) + "\n")

    print(f"Read {len(rows)} rows")
    print(f"Used top {keep_count} rows ({args.top_percent}%)")
    print(f"Wrote {args.output}")
    print(json.dumps(params, indent=2))


if __name__ == "__main__":
    main()