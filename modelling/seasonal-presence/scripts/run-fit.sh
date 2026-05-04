#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname SPECIES
    exit 1
fi

# Set the environment
MODELLING_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
PROJECT_FOLDER=$( cd "$MODELLING_FOLDER/../.." && pwd)
RUN_ODE_SOLVER="$PROJECT_FOLDER/scripts/run-solver.sh"
SIMULATION_FILE="$MODELLING_FOLDER/model/seasonal_presence_generic.json"
OBSERVED_CSV="$MODELLING_FOLDER/data/$1_observed.csv"
PARAMETERS_CSV="$MODELLING_FOLDER/data/$1_parameters.csv"
PARAMETERS_JSON="$MODELLING_FOLDER/data/$1_best.json"

echo "Modelling Folder   : $MODELLING_FOLDER"
echo "ODE Solver Command : $RUN_ODE_SOLVER"
echo "Observed Data File : $OBSERVED_CSV"
echo "Simulation File    : $SIMULATION_FILE"
echo "Parameters File    : $PARAMETERS_CSV"

# Run the fit
python "$MODELLING_FOLDER/scripts/parameter_fitting.py" \
    --observed "$OBSERVED_CSV" \
    --simulation "$SIMULATION_FILE" \
    --solver-command "$RUN_ODE_SOLVER" \
    --csv "$PARAMETERS_CSV" \
    --runs 20 \
    --best-output "$PARAMETERS_JSON"
