#!/usr/bin/env bash

if (( $# < 2 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname PROJECT CLUSTERS [WRITE-CSV]
    exit 1
fi

# Get the path to the modelling folder
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )

# Activate the virtuall environment
PROJECT_FOLDER=$( cd "$MODELLING_ROOT/.." && pwd)
source "$PROJECT_FOLDER/venv/bin/activate"

# Build the paths to the per-model data folders and the analysis output folder
ANALYSIS_FOLDER="$MODELLING_ROOT/data/$1/analysis"
RESIDENT_DATA="$MODELLING_ROOT/data/$1/resident"
SEASONAL_DATA="$MODELLING_ROOT/data/$1/seasonal"
WINTER_DATA="$MODELLING_ROOT/data/$1/winter"

if [[ ! -d "$RESIDENT_DATA" ]]; then
    echo Data folder not found: $RESIDENT_DATA
    exit 1
fi

if [[ ! -d "$SEASONAL_DATA" ]]; then
    echo Data folder not found: $SEASONAL_DATA
    exit 1
fi

if [[ ! -d "$WINTER_DATA" ]]; then
    echo Data folder not found: $WINTER_DATA
    exit 1
fi

# Set the arguments to write the CSV file
WRITE_CSV=""
if (( $# == 3 )); then
    # Get the first argument in lowercase
    value=$(printf '%s' "$3" | tr '[:upper:]' '[:lower:]')

    # If it's truthy, set the CSV output arguments. Otherwise, make them blank
    case "$value" in
        true|yes|y|1)
            WRITE_CSV="--output-csv $ANALYSIS_FOLDER/feature_matrix.csv"
            ;;
        false|no|n|0)
            WRITE_CSV=""
            ;;
        *)
            echo "'$3' is not a valid value for WRITE-CSV"
            exit 1
            ;;
    esac
fi

# Build the feature matrix, similarity and clustering pipeline
python "$MODELLING_ROOT/src/feature-matrix.py" \
    --input  "$RESIDENT_DATA" "$SEASONAL_DATA" "$WINTER_DATA" \
    --json "$ANALYSIS_FOLDER/feature_matrix.json" \
    --similarity "$ANALYSIS_FOLDER/species_similarity.json" \
    --similarity-summary "$ANALYSIS_FOLDER/species_similarity.txt" \
    --heatmap "$ANALYSIS_FOLDER/species_similarity_heatmap.png" \
    --number-of-clusters $2 \
    --clusters "$ANALYSIS_FOLDER/cluster_analysis.json" \
    --cluster-summary "$ANALYSIS_FOLDER/cluster_summary.txt" \
    --dendrogram "$ANALYSIS_FOLDER/cluster_dendrogram.png"$WRITE_CSV
