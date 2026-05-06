#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname SPECIES
    exit 1
fi

MODELLING_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
DATA_FOLDER="$MODELLING_FOLDER/data"

rm -f "$DATA_FOLDER/$1_consensus.json"
rm -f "$DATA_FOLDER/$1_parameters.csv"
rm -f "$DATA_FOLDER/$1_simulated.csv"
rm -f "$DATA_FOLDER/$1_simulated.png"
rm -f "$DATA_FOLDER/$1_synthesised.csv"
rm -f "$DATA_FOLDER/$1_synthesised.png"
