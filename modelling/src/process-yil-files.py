import argparse
import os
import pandas as pd
from pathlib import Path

TRUE_VALUES = ["true", "yes", "y", "1"]
FALSE_VALUES = ["false", "no", "n", "0"]

SUFFIXES = [
    "_abingdon",
    "_abingdon_butterfly_flight_period",
    "_thrupp_lake"
]


def rename_year_in_life_files(folder_path: str, pattern: str, new_suffix: str) -> None:
    """
    Rename 'year in the life' formatted file names to <species>_observed.xlsx

    :param folder_path: Path to the folder containing the file
    :param pattern: XLSX file pattern to match
    :param new_suffix: Renamed XLSX file suffix, excluding extension
    """
    directory = Path(folder_path)
    for filepath in directory.glob(pattern):
        # Extract species (equivalent to bash parameter expansion)
        filename = filepath.stem
        species = filename.removeprefix("year_in_the_life_")
        print(species)
        for suffix in SUFFIXES:
            print(f"Removing {suffix}")
            species = species.removesuffix(suffix)

        # Create the new file name and path
        new_name = f"{species}{new_suffix}.xlsx"
        new_path = filepath.with_name(new_name)

        # Perform the rename
        os.rename(filepath, new_path)
        print(f"{filename} -> {new_name}")


def extract_observed_data(folder_path: str, suffix: str) -> None:
    """
    Extract 'year in the life' presence data from a set of XLSX files into
    equivalently-named CSV files suitable for model fitting

    :param folder_path: Path to the folder containing the file
    :param suffix: XLSX file suffix, excluding extension
    """
    # Iterate over the files in the specified path
    matches = []
    directory = Path(folder_path)
    for filepath in directory.glob(f"*{suffix}.xlsx"):
        # Add this file to the matched files
        matches.append(filepath)

        # Extract species name
        filename = filepath.name
        species = filename.replace("_observed.xlsx", "")

        # Read the "Presence" sheet, select the 2nd and 3rd columns and rename them
        df = pd.read_excel(filepath, sheet_name="Presence")
        df_subset = df.iloc[:, [1, 2]].copy()
        df_subset.columns = ["month", "value"]

        # Save the resulting data frame to CSV
        output_file = directory / f"{species}_observed.csv"
        df_subset.to_csv(output_file, index=False)

        print(f"Processed: {filename} -> {output_file.name}")

    return matches


def delete_files(file_paths: list) -> None:
    """
    Delete a collection of files

    :param file_paths: List of files to delete
    """
    for filepath in file_paths:
        try:
            filepath.unlink()
            print(f"Deleted: {filepath.name}")
        except Exception as e:
            print(f"Failed to delete {filepath.name}: {e}")


def main():
    # Parse the command line arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--input", required=True,
                        help="Path to the folder containing the 'Year In The Life' XLSX files")
    parser.add_argument("-xp", "--xlsx-pattern", default="*.xlsx", help="XLSX file pattern")
    parser.add_argument("-s", "--suffix", default="_observed", help="CSV file name suffix")
    parser.add_argument("-d", "--delete", type=str.lower, choices=TRUE_VALUES + FALSE_VALUES,
                        help="Delete XLSX files after processing")
    args = parser.parse_args()

    # Rename the 'Year In The Life' XLSX files, extract the observed 'Presence' data and delete the
    # original XLSX files
    rename_year_in_life_files(args.input, args.xlsx_pattern, args.suffix)
    xlsx_files = extract_observed_data(args.input, args.suffix)
    if args.delete in TRUE_VALUES:
        delete_files(xlsx_files)


if __name__ == "__main__":
    main()
