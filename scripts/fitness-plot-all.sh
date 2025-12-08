#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <results_directory>"
    exit 1
fi

FOLDERS=("$1"/*)

for folder in "${FOLDERS[@]}"; do
    if [ ! -d "$folder" ]; then
        continue
    fi
    echo "Processing folder: $folder"
    python3 scripts/fitness-plot.py \
        "$folder" \
        --bins 40 \
        --save "$(basename "$folder")-syntactic-hist.png" \
        --property syntactic
done
