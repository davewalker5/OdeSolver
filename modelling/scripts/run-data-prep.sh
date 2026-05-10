#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname FOLDER
    exit 1
fi

# Get the path to the modelling folder and the project root
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )
PROJECT_FOLDER=$( cd "$MODELLING_ROOT/.." && pwd)

# Activate the virtual environment
source "$PROJECT_FOLDER/venv/bin/activate"

python "$MODELLING_ROOT/src/process-yil-files.py" --input "$1" --delete true
