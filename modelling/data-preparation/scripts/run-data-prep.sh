#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname FOLDER
    exit 1
fi

DATA_PREP_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )
source "$DATA_PREP_FOLDER/venv/bin/activate"

python "$DATA_PREP_FOLDER/src/process-yil-files.py" --input "$DATA_PREP_FOLDER/pending/$1" --delete true
