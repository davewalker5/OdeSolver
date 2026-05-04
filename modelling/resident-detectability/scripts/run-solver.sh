#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname SPECIES
    exit 1
fi

# Set the environment
MODELLING_FOLDER=$( cd "$(dirname "$0")/.." ; pwd -P )
PROJECT_ROOT=$( cd "$MODELLING_FOLDER/../.." ; pwd -P )
DATA_FOLDER="$MODELLING_FOLDER/data"
export PYTHONPATH="$PROJECT_ROOT/src"
source "$PROJECT_ROOT/venv/bin/activate"

# Set the path to the parameters file - this is the in the "data" folder and is expected
# to be the result of a consensus calculation on parameter fitting results. It should be
# called SPECIES_consensus.json
export SEASONAL_PARAMS_FILE="$MODELLING_FOLDER/data/$1_consensus.json"

echo "Model Folder    : $MODELLING_FOLDER"
echo "Project Folder  : $PROJECT_ROOT"
echo "PYTHONPATH      : $PYTHONPATH"
echo "Parameters File : $SEASONAL_PARAMS_FILE"

python -m ode_solver \
    --simulation "$MODELLING_FOLDER/model/resident_detectability_generic.json" \
    --auto-run \
    --export "$DATA_FOLDER/$1_simulated.csv" \
    --chart "$DATA_FOLDER/$1_simulated.png" \
    --no-gui \
    --normalise false \
    --quiet
