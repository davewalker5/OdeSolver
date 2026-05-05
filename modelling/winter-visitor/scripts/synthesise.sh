#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname SPECIES
    exit 1
fi

# Set the environment
MODELLING_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
OBSERVED_CSV="$MODELLING_FOLDER/data/$1_observed.csv"
SIMULATED_CSV="$MODELLING_FOLDER/data/$1_simulated.csv"
SYNTHESISED_CSV="$MODELLING_FOLDER/data/$1_synthesised.csv"
SYNTHESISED_PNG="$MODELLING_FOLDER/data/$1_synthesised.png"

echo "Modelling Folder       : $MODELLING_FOLDER"
echo "Observed Data File     : $OBSERVED_CSV"
echo "Simulated Data File    : $SIMULATION_FILE"
echo "Synthesised Data File  : $SYNTHESISED_CSV"
echo "Synthesised Chart File : $SYNTHESISED_PNG"
echo

# Run the fit
python "$MODELLING_FOLDER/scripts/synthesise_simulated_curve.py" \
    --observed "$OBSERVED_CSV" \
    --simulated "$SIMULATED_CSV" \
    --output-csv "$SYNTHESISED_CSV" \
    --plot "$SYNTHESISED_PNG"
