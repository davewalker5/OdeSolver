#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname MODEL
    exit 1
fi

# Get the path to the modelling folder and the project root
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )

# Set the model=specific environment
case "$1" in
    resident)
        MODEL_FOLDER="$MODELLING_ROOT/resident-detectability"
        ;;
    seasonal)
        MODEL_FOLDER="$MODELLING_ROOT/seasonal-presence"
        ;;
    winter)
        MODEL_FOLDER="$MODELLING_ROOT/winter-visitor"
        ;;
    *)
        echo "Unrecognised model '$1'"
        exit 1
        ;;
esac

# Build the species list - a species needs to be modelled if it's "observed" data file is
# present but the simulated output isn;t
species_list=()
for observed_file in "$MODEL_FOLDER"/data/*_observed.csv; do
    [[ -e "$observed_file" ]] || continue

    filename=$(basename "$observed_file")
    species=${filename%_observed.csv}
    simulated_file="$MODEL_FOLDER/data/${species}_simulated.csv"

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
    "$MODELLING_ROOT/scripts/run-fit.sh" $1 "$species"
done
