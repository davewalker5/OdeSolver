#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname SPECIES
    exit 1
fi

if [[ -z "${RUN_ODE_SOLVER+x}" ]]; then
  echo "The RUN_ODE_SOLVER environment variable must be set with the path to the ODE Solver run script"
  exit 1
fi

# Set the environment
MODELLING_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
SIMULATION_FILE="$MODELLING_FOLDER/model/seasonal_presence_generic.json"
OBSERVED_CSV="$MODELLING_FOLDER/data/$1_observed.csv"
PARAMETERS_CSV="$MODELLING_FOLDER/data/$1_parameters.csv"

echo "Modelling Folder   : $MODELLING_FOLDER"
echo "ODE Solver Command : $SEASONAL_PARAMS_FILE"
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
    --best-output "$MODELLING_FOLDER/data/best_params.json" \
