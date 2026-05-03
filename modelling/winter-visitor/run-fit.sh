#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname OBSERVED_CSV_FILE
    exit 1
fi

if [[ -z "${RUN_ODE_SOLVER+x}" ]]; then
  echo "The RUN_ODE_SOLVER environment variable must be set with the path to the ODE Solver run script"
  exit 1
fi

# Get the project root folder
export MODELLING_ROOT=$( cd "$( dirname "$0" )" && pwd )
SIMULATION_FILE="$MODELLING_ROOT/simulations/winter_visitor_generic.json"
PARAMETERS_CSV="$MODELLING_ROOT/example/redwing_parameters.csv"

# Run the fit
python "$MODELLING_ROOT/parameter_fitting.py" \
    --observed "$1" \
    --simulation "$SIMULATION_FILE" \
    --solver-command "$RUN_ODE_SOLVER" \
    --csv "$PARAMETERS_CSV" \
    --runs 20
