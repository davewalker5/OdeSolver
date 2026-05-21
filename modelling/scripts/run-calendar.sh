#!/usr/bin/env bash

if (( $# != 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname PROJECT
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

# Build the ecological calendar pipeline
python "$MODELLING_ROOT/src/eco-calendar.py" \
    --input  "$RESIDENT_DATA" "$SEASONAL_DATA" "$WINTER_DATA" \
    --clusters "$ANALYSIS_FOLDER/cluster_analysis.json" \
    --extracted "$ANALYSIS_FOLDER/extracted_clusters.json" \
    --activity "$ANALYSIS_FOLDER/calendar_activity.json" \
    --heatmap "$ANALYSIS_FOLDER/activity_heatmap.png"
