#!/usr/bin/env bash

if (( $# != 2 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname MODEL SPECIES
    exit 1
fi

# Get the path to the modelling folder and the project root
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )
PROJECT_FOLDER=$( cd "$MODELLING_ROOT/.." && pwd)

# Set the model=specific environment
case "$1" in
    resident)
        MODEL_FOLDER="$MODELLING_ROOT/resident-detectability"
        MODEL="resident_detectability_generic.json"
        ;;
    seasonal)
        MODEL_FOLDER="$MODELLING_ROOT/seasonal-presence"
        MODEL="seasonal_presence_generic.json"
        ;;
    winter)
        MODEL_FOLDER="$MODELLING_ROOT/winter-visitor"
        MODEL="winter_visitor_generic.json"
        ;;
    *)
        echo "Unrecognised model '$1'"
        exit 1
        ;;
esac

# Run the fit
python "$MODELLING_ROOT/src/$1.py" \
    --species "$2" \
    --observed "$MODEL_FOLDER/data/$2_observed.csv" \
    --simulation "$MODEL_FOLDER/model/$MODEL" \
    --solver-command "$PROJECT_FOLDER/scripts/run-solver.sh" \
    --csv "$MODEL_FOLDER/data/$2_parameters.csv" \
    --consensus-json "$MODEL_FOLDER/data/$2_consensus.json" \
    --export-simulated "$MODEL_FOLDER/data/$2_simulated.csv" \
    --plot-simulated "$MODEL_FOLDER/data/$2_simulated.png" \
    --export-synthesised "$MODEL_FOLDER/data/$2_synthesised.csv" \
    --plot-synthesised "$MODEL_FOLDER/data/$2_synthesised.png"
