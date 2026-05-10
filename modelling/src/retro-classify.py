import argparse
from pathlib import Path
from datetime import datetime

from seasonal.classification.resident import classify_resident_model_to_json
from seasonal.classification.seasonal import classify_seasonal_model_to_json
from seasonal.classification.winter import classify_winter_model_to_json
from seasonal.support.json import load_json

RESIDENT = "resident"
SEASONAL = "seasonal"
WINTER = "winter"

MODEL_FOLDERS = {
    RESIDENT: "resident-detectability",
    SEASONAL: "seasonal-presence",
    WINTER: "winter-visitor"
}

CONSENSUS_SUFFIX = "_consensus.json"


def print_message(message):
    """
    Print a timestamped message

    :param message: Message
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} : {message}")


def print_error(message):
    """
    Print a timestamped error message

    :param message: Error message
    """
    print_message(f"ERROR : {message}")


def classify_species(data_folder: Path, model: str, species: str) -> None:
    """
    Classify a species given its name and the model it belongs to

    :param data_folder: Path to the data folder for the model
    :param model: Model name
    :param species: Species name
    """
    print_message(f"Classifying {species} for model {model}")

    # Remove any existing file
    classification_file = data_folder / f"{species}_classification.json"
    classification_file.unlink(missing_ok=True)

    # Determine the path to the consensus parameters file
    consensus_file = data_folder / f"{species}_consensus.json"
    if consensus_file.exists():
        # Load the consensus parameters and classify the species
        parameters = load_json(consensus_file)
        if model == RESIDENT:
            classify_resident_model_to_json(parameters, classification_file)
        elif model == SEASONAL:
            classify_seasonal_model_to_json(parameters, classification_file)
        else:
            classify_winter_model_to_json(parameters, classification_file)

        print_message(f"Written classification file {classification_file.name}")
    else:
        print_error(f"Consensus file for {species} not found")


def classify_all_species(data_folder: Path, model: str) -> None:
    # Find all the consensus files in the data folder
    for consensus_file in data_folder.glob(f"*{CONSENSUS_SUFFIX}"):
        # Determine the species name and classify it
        species = consensus_file.stem.replace("_consensus", "")
        classify_species(data_folder, model, species)


def main():
    """
    Main entry point for the retrospective classifier
    """
    parser = argparse.ArgumentParser()

    parser.add_argument("-m", "--model", choices=[RESIDENT, SEASONAL, WINTER], required=True, help="Model name")
    parser.add_argument("-s", "--species", help="Species name")
    parser.add_argument("-a", "--all", action="store_true", help="Classify all species for the specied model")
    args = parser.parse_args()

    # Calculate the path to the models data folder
    data_folder = Path(__file__).parent.parent / MODEL_FOLDERS[args.model] / "data"

    if args.all:
        classify_all_species(data_folder, args.model)
    elif args.species:
        classify_species(data_folder, args.model, args.species)
    else:
        print_error("You must specify a species or the 'all' flag")


if __name__ == "__main__":
    main()
