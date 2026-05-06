#!/usr/bin/env bash

MODELLING_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
DATA_FOLDER="$MODELLING_FOLDER/data"

rm -f "$DATA_FOLDER"/*_consensus.json
rm -f "$DATA_FOLDER"/*_parameters.csv
rm -f "$DATA_FOLDER"/*_simulated.csv
rm -f "$DATA_FOLDER"/*_simulated.png
rm -f "$DATA_FOLDER"/*_synthesised.csv
rm -f "$DATA_FOLDER"/*_synthesised.png
