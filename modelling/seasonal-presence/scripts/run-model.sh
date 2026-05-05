#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname SPECIES
    exit 1
fi

MODELLING_FOLDER=$( cd "$( dirname "$0" )/.." && pwd )

# Define output files and initialise the success/fail flag
species="$1"
fit_output="data/${species}_parameters.csv"
consensus_output="data/${species}_consensus.json"
simulated_output="data/${species}_simulated.csv"
species_failed=0

# Run the parameter fitting
"$MODELLING_FOLDER/scripts/run-fit.sh" "$species"
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
    "$MODELLING_FOLDER/scripts/run-consensus.sh" "$species"
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
        "$MODELLING_FOLDER/scripts/run-solver.sh" "$species"
        solver_status=$?
        timestamp=$(date "+%Y-%m-%d %H:%M:%S")

        if [[ $solver_status -ne 0 ]]; then
            echo "$timestamp : WARNING : Solver failed for $species (exit code: $solver_status)"
            species_failed=1
        elif [[ ! -f "$simulated_output" ]]; then
            echo "$timestamp : WARNING : Simulation completed for $species, but expected output was not found: $simulated_output"
            species_failed=1
        else
            # Run the data synthesis for this species
            "$MODELLING_FOLDER/scripts/synthesise.sh" "$species"
            synthesis_status=$?
            timestamp=$(date "+%Y-%m-%d %H:%M:%S")

            if [[ $synthesis_status -ne 0 ]]; then
                echo "$timestamp : WARNING : Data synthesis failed for $species (exit code: $synthesis_status)"
                species_failed=1
            fi
        fi
    fi
fi

# Output the final success/fail message
timestamp=$(date "+%Y-%m-%d %H:%M:%S")
if [[ $species_failed -ne 0 ]]; then
    echo "$timestamp : ERROR : Failed to process $species"
else
    echo "$timestamp : INFO : Successfully processed $species"
fi
