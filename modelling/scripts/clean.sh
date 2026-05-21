#!/usr/bin/env bash

if (( $# != 3 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname PROJECT MODEL SPECIES
    exit 1
fi

# Get the path to the modelling folder and the project root
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )

# Construct the path to the model-specific data folder for the specified project
# and check the folder exists
DATA_FOLDER="$MODELLING_ROOT/data/$1/$2"
if [[ ! -d "$DATA_FOLDER" ]]; then
    echo Data folder not found: $DATA_FOLDER
    exit 1
fi

rm -f "$DATA_FOLDER/$3_classification.json"
rm -f "$DATA_FOLDER/$3_consensus.json"
rm -f "$DATA_FOLDER/$3_parameters.csv"
rm -f "$DATA_FOLDER/$3_simulated.csv"
rm -f "$DATA_FOLDER/$3_simulated.png"
rm -f "$DATA_FOLDER/$3_synthesised.csv"
rm -f "$DATA_FOLDER/$3_synthesised.png"
