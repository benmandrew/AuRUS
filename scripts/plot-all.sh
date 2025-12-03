#!/bin/bash

FOLDERS=(./25-12-02-ltl-filter-arbiter/*)

for folder in "${FOLDERS[@]}"; do
    if [ ! -d "$folder" ]; then
        continue
    fi
    echo "Processing folder: $folder"
    python3 scripts/fitness-plot.py "$folder" --bins 40 --save "$(basename "$folder")-fitness-hist.png"
done
