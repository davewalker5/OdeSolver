#!/usr/bin/env bash

if (( $# != 3 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname PROJECT MODEL SPECIES
    exit 1
fi

# Get the path to the modelling folder and the project root
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )
PROJECT_FOLDER=$( cd "$MODELLING_ROOT/.." && pwd)
DATA_FOLDER="$MODELLING_ROOT/data/$1/$2/"

# Set the model=specific environment
case "$2" in
    resident)
        MODEL="$MODELLING_ROOT/models/$2/resident_detectability_generic.json"
        ;;
    seasonal)
        MODEL="$MODELLING_ROOT/models/$2/seasonal_presence_generic.json"
        ;;
    winter)
        MODEL="$MODELLING_ROOT/models/$2/winter_visitor_generic.json"
        ;;
    *)
        echo "Unrecognised model '$2'"
        exit 1
        ;;
esac

# Run the fit
python "$MODELLING_ROOT/src/$2.py" \
    --species "$3" \
    --observed "$DATA_FOLDER/$3_observed.csv" \
    --simulation "$MODEL" \
    --solver-command "$PROJECT_FOLDER/scripts/run-solver.sh" \
    --csv "$DATA_FOLDER/$3_parameters.csv" \
    --consensus-json "$DATA_FOLDER/$3_consensus.json" \
    --classification-json "$DATA_FOLDER/$3_classification.json" \
    --export-simulated "$DATA_FOLDER/$3_simulated.csv" \
    --plot-simulated "$DATA_FOLDER/$3_simulated.png" \
    --export-synthesised "$DATA_FOLDER/$3_synthesised.csv" \
    --plot-synthesised "$DATA_FOLDER/$3_synthesised.png"
