#!/usr/bin/env bash

if (( $# > 1 )); then
    scriptname=$(basename -- "$0")
    echo Usage: $scriptname [WRITE-CSV]
    exit 1
fi

# Get the path to the modelling folder
MODELLING_ROOT=$( cd "$( dirname "$0" )/.." && pwd )

# Activate the virtuall environment
PROJECT_FOLDER=$( cd "$MODELLING_ROOT/.." && pwd)
source "$PROJECT_FOLDER/venv/bin/activate"

# Build the paths to the per-model data folders
RESIDENT_DATA="$MODELLING_ROOT/resident-detectability/data"
SEASONAL_DATA="$MODELLING_ROOT/seasonal-presence/data"
WINTER_DATA="$MODELLING_ROOT/winter-visitor/data"

# Build the ecological calendar pipeline
python "$MODELLING_ROOT/src/eco-calendar.py" \
    --input  "$RESIDENT_DATA" "$SEASONAL_DATA" "$WINTER_DATA" \
    --clusters "$MODELLING_ROOT/data/cluster_analysis.json" \
    --extracted "$MODELLING_ROOT/data/extracted_clusters.json" \
    --activity "$MODELLING_ROOT/data/calendar_activity.json" \
    --heatmap "$MODELLING_ROOT/data/activity_heatmap.png"
