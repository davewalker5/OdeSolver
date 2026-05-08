from pathlib import Path
import json

from seasonal.classification.resident import classify_resident_model_to_json


CONSENSUS_DIR = Path(__file__).parent.parent / "resident-detectability" / "data"

for consensus_file in CONSENSUS_DIR.glob("*_consensus.json"):

    species = consensus_file.stem.replace("_consensus", "")

    classification_file = (
        consensus_file.parent /
        f"{species}_classification.json"
    )

    with open(consensus_file, "rt", encoding="utf-8") as f:
        parameters = json.load(f)

    print(f"Classifying: {species}")

    classify_resident_model_to_json(
        parameters=parameters,
        output_path=classification_file,
    )

    print(f"  -> {classification_file}")
