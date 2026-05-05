#!/usr/bin/env bash

# Build the species list - a species needs to be modelled if it's "observed" data file is
# present but the simulated output isn;t
species_list=()
for observed_file in data/*_observed.csv; do
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

    fit_output="data/${species}_parameters.csv"
    consensus_output="data/${species}_consensus.json"

    species_failed=0

    # Run the parameter fitting
    ./scripts/run-fit.sh "$species"
    fit_status=$?
    timestamp=$(date "+%Y-%m-%d %H:%M:%S")

    if [[ $fit_status -ne 0 ]]; then
        echo "$timestamp : WARNING : Fit failed for $species (exit code: $fit_status)"
        species_failed=1
    elif [[ ! -f "$fit_output" ]]; then
        echo "$timestamp : WARNING : Fit completed for $species, but expected output was not found: $fit_output"
        species_failed=1
    else
        # Generate the consensus parameter file for this species
        ./scripts/run-consensus.sh "$species"
        consensus_status=$?
        timestamp=$(date "+%Y-%m-%d %H:%M:%S")

        if [[ $consensus_status -ne 0 ]]; then
            echo "$timestamp : WARNING : Consensus failed for $species (exit code: $consensus_status)"
            species_failed=1
        elif [[ ! -f "$consensus_output" ]]; then
            echo "$timestamp : WARNING : Consensus completed for $species, but expected output was not found: $consensus_output"
            species_failed=1
        else
            # Run the ODE solver for this species
            ./scripts/run-solver.sh "$species"
            solver_status=$?
            timestamp=$(date "+%Y-%m-%d %H:%M:%S")

            if [[ $solver_status -ne 0 ]]; then
                echo "$timestamp : WARNING : Solver failed for $species (exit code: $solver_status)"
                species_failed=1
            fi
        fi
    fi

    timestamp=$(date "+%Y-%m-%d %H:%M:%S")
    if [[ $species_failed -ne 0 ]]; then
        echo "$timestamp : ERROR : Failed to process $species"
    else
        echo "$timestamp : INFO : Successfully processed $species"
    fi
done
