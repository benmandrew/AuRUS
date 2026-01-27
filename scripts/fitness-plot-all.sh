#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <results_directory> <property>"
    exit 1
fi

if [ ! -d "$1" ]; then
    echo "Error: Directory '$1' does not exist."
    exit 1
fi

if [ "$2" != "fitness" ] && [ "$2" != "semantic" ] && [ "$2" != "syntactic" ]; then
    echo "Error: Second argument must be either 'fitness', 'semantic', or 'syntactic'."
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
        --save "$(basename "$folder")-$2-hist.png" \
        --property "$2"
done
