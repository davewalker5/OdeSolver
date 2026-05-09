#!/usr/bin/env bash

if (( $# < 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname MODEL [SPECIES]
    exit 1
fi

# Get the path to the modelling folder
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )

# Run the classifier
if (( $# == 1 )); then
    python "$MODELLING_ROOT/src/retro-classify.py" --model "$1" --all
else
    python "$MODELLING_ROOT/src/retro-classify.py" --model "$1" --species "$2"
fi