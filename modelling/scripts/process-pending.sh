#!/usr/bin/env bash

if (( $# != 2 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname PROJECT MODEL
    exit 1
fi

# Get the path to the modelling folder and the project root
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )

# Construct the path to the model-specific data folder for the specified project
# and check the folder exists
DATA_FOLDER="$MODELLING_ROOT/data/$1/$2"
if [[ ! -d "$DATA_FOLDER" ]]; then
    echo Data folder not found: $DATA_FOLDER
    exit 1
fi

# Build the species list - a species needs to be modelled if it's "observed" data file is
# present but the simulated output isn;t
species_list=()
for observed_file in "$DATA_FOLDER"/*_observed.csv; do
    [[ -e "$observed_file" ]] || continue

    filename=$(basename "$observed_file")
    species=${filename%_observed.csv}
    simulated_file="$DATA_FOLDER/${species}_simulated.csv"

    if [[ ! -f "$simulated_file" ]]; then
        species_list+=("$species")
    fi
done

# Check there are some species to process
if [[ ${#species_list[@]} -eq 0 ]]; then
    echo "No pending species found."
    exit 0
fi

# Iterate over the species that need processing
for species in "${species_list[@]}"; do
    "$MODELLING_ROOT/scripts/run-fit.sh" "$1" "$2" "$species"
done
