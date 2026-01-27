#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <results_directory>"
    exit 1
fi

for dir in "$1"/*/; do
    echo "Results for directory: $dir"
    ./scripts/read-results.sh "$dir"
    echo ""
done
