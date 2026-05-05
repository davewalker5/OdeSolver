#!/usr/bin/env bash

MODELLING_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )

# Build the species list - a species needs to be modelled if it's "observed" data file is
# present but the simulated output isn;t
species_list=()
for observed_file in "$MODELLING_FOLDER"/data/*_observed.csv; do
    [[ -e "$observed_file" ]] || continue

    filename=$(basename "$observed_file")
    species=${filename%_observed.csv}
    simulated_file="data/${species}_simulated.csv"

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
    echo "----------------------------------------------------------------------------------------"
    echo "Processing: $species"

    "$MODELLING_FOLDER/scripts/run-model.sh" "$species"
done
