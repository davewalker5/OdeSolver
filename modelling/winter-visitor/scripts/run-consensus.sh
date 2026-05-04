#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname SPECIES
    exit 1
fi

MODELLING_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
python "$MODELLING_FOLDER/scripts/consensus-parameters.py" \
    --input "$MODELLING_FOLDER/data/$1_parameters.csv" \
    --output "$MODELLING_FOLDER/data/$1_consensus.json"
