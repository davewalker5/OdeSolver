#!/usr/bin/env bash

if (( $# != 2 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname MODEL SPECIES
    exit 1
fi

# Get the path to the modelling folder and the project root
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )

# Set the model=specific environment
case "$1" in
    resident)
        MODEL_FOLDER="$MODELLING_ROOT/resident-detectability"
        ;;
    seasonal)
        MODEL_FOLDER="$MODELLING_ROOT/seasonal-presence"
        ;;
    winter)
        MODEL_FOLDER="$MODELLING_ROOT/winter-visitor"
        ;;
    *)
        echo "Unrecognised model '$1'"
        exit 1
        ;;
esac

rm -f "$MODEL_FOLDER/data/$2_classification.json"
rm -f "$MODEL_FOLDER/data/$2_consensus.json"
rm -f "$MODEL_FOLDER/data/$2_parameters.csv"
rm -f "$MODEL_FOLDER/data/$2_simulated.csv"
rm -f "$MODEL_FOLDER/data/$2_simulated.png"
rm -f "$MODEL_FOLDER/data/$2_synthesised.csv"
rm -f "$MODEL_FOLDER/data/$2_synthesised.png"
