#!/usr/bin/env bash

if (( $# > 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname [WRITE-CSV]
    exit 1
fi


# Get the path to the modelling folder
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )

# Build the paths to the per-model data folders
RESIDENT_DATA="$MODELLING_ROOT/resident-detectability/data"
SEASONAL_DATA="$MODELLING_ROOT/seasonal-presence/data"
WINTER_DATA="$MODELLING_ROOT/winter-visitor/data"

# Set the arguments to write the CSV file
WRITE_CSV=""
if (( $# == 1 )); then
    # Get the first argument in lowercase
    value=$(printf '%s' "$1" | tr '[:upper:]' '[:lower:]')

    # If it's truthy, set the CSV output arguments. Otherwise, make them blank
    case "$value" in
        true|yes|y|1)
            WRITE_CSV="--output-csv $MODELLING_ROOT/data/feature_matrix.csv"
            ;;
        false|no|n|0)
            WRITE_CSV=""
            ;;
        *)
            echo "'$1' is not a valid value for WRITE-CSV"
            exit 1
            ;;
    esac
fi

# Build the feature matrix
python "$MODELLING_ROOT/src/feature_matrix.py" \
    --input  "$RESIDENT_DATA" "$SEASONAL_DATA" "$WINTER_DATA" \
    --output-json "$MODELLING_ROOT/data/feature_matrix.json" $WRITE_CSV
