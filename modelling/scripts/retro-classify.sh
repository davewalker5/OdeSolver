#!/usr/bin/env bash

if (( $# < 2 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname PROJECT MODEL [SPECIES]
    exit 1
fi

# Get the path to the modelling folder
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )

# Run the classifier
if (( $# == 2 )); then
    python "$MODELLING_ROOT/src/retro-classify.py" --project "$1" --model "$2" --all
else
    python "$MODELLING_ROOT/src/retro-classify.py" --project "$1" --model "$2" --species "$3"
fi