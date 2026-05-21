#!/usr/bin/env bash

if (( $# != 2 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname PROJECT MODEL
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

rm -f "$DATA_FOLDER"/*_classification.json
rm -f "$DATA_FOLDER"/*_consensus.json
rm -f "$DATA_FOLDER"/*_parameters.csv
rm -f "$DATA_FOLDER"/*_simulated.csv
rm -f "$DATA_FOLDER"/*_simulated.png
rm -f "$DATA_FOLDER"/*_synthesised.csv
rm -f "$DATA_FOLDER"/*_synthesised.png
