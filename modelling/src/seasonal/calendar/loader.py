from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

SUFFIX = "_synthesised"


def load_synthesised_species_data(folders: list[str | Path]) -> list[dict[str, Any]]:
    """
    Load and combine all <species>_synthesised.csv files from the supplied folders. Adds a canonical
    'Species' field derived from the filename

    :param folders: List of folder paths containing simulated CSV files
    """
    all_rows: list[dict[str, Any]] = []

    for folder in folders:
        folder = Path(folder)

        for csv_path in sorted(folder.glob(f"*{SUFFIX}.csv")):
            species_name = _species_name_from_filename(csv_path)

            with csv_path.open("r", encoding="utf-8") as f:
                reader = csv.DictReader(f)

                for row in reader:
                    row["Species"] = species_name
                    all_rows.append(row)

    return all_rows


def _species_name_from_filename(path: Path) -> str:
    """
    Convert a filename <species>_synthesised.csv to a species name. The <species> element
    if lowercase and uses "_" as the word separator rather than a space

    :param path: Path to the CSV file
    :return: Species name
    """

    stem = path.stem

    if stem.endswith(f"{SUFFIX}"):
        stem = stem[:-len(SUFFIX)]

    return stem.replace("_", " ").title()
