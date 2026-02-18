#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

#######################################
# Remove non-maximal specs from output directory.
# Globals:
#   None
# Arguments:
#   Output directory path
#######################################
remove_non_maximal_specs() {
    local out_dir="$1"
    local maximal_file="$out_dir/maximal-specs.txt"
    local -a max_specs
    local -A keep_specs
    if [[ ! -f "$maximal_file" ]]; then
        echo "Maximal specs file not found: $maximal_file" >&2
        return 1
    fi
    mapfile -t max_specs < "$maximal_file"
    if [[ ${#max_specs[@]} -eq 0 ]]; then
        echo "No maximal specs found in $maximal_file" >&2
        return 1
    fi
    local spec_path
    for spec_path in "${max_specs[@]}"; do
        keep_specs["$(basename "$spec_path")"]=1
    done
    find "$out_dir" -maxdepth 1 -type f -name "*.tlsf" -print0 | \
        while IFS= read -r -d '' spec; do
            local spec_name
            spec_name="$(basename "$spec")"
            if [[ -z "${keep_specs[$spec_name]+x}" ]]; then
                rm -f "$spec"
            fi
        done
}

#######################################
# Check that all spec files exist and print status.
# Globals:
#   None
# Arguments:
#   Name of array variable containing spec file paths
#######################################
check_spec_files_exist() {
    local -n specs_ref="$1"
    local missing_any=false
    local case_study_spec
    for case_study_spec in "${specs_ref[@]}"; do
        if [[ -f "$case_study_spec" ]]; then
            printf '\033[32m✓\033[0m %s\n' "$case_study_spec"
        else
            printf '\033[31m✗\033[0m %s\n' "$case_study_spec" >&2
            missing_any=true
        fi
    done
    if [[ "$missing_any" == true ]]; then
        return 1
    fi
}

ant compile > /dev/null

# Fitness factors (as percentage)
REAL=70
SYNTACTIC=10
WEAK=10
STRONG=10
# Convert percentages to factors between 0 and 1
FACTORS="-factors=$(bc<<<"scale=2; ${REAL}/100"),$(bc<<<"scale=2; ${SYNTACTIC}/100"),$(bc<<<"scale=2; ${WEAK}/100"),$(bc<<<"scale=2; ${STRONG}/100")"

N_RUNS=30
FLAGS=(-Max=1000 -Gen=1000 -Pop=100 -k=10 -GATO=7200 -addA)
OUT_DIR=result
SPEC_LIST_FILE="case-study-specs.txt"
if [[ ! -f "$SPEC_LIST_FILE" ]]; then
    echo "Spec list file not found: $SPEC_LIST_FILE" >&2
    exit 1
fi
mapfile -t CASE_STUDY_SPECS < "$SPEC_LIST_FILE"

if ! check_spec_files_exist CASE_STUDY_SPECS; then
    exit 1
fi

CSV_FILE="$OUT_DIR/run-times.csv"
mkdir -p "$OUT_DIR"
if [[ ! -f "$CSV_FILE" ]]; then
    echo "case_study,run_index,unreal_repair_seconds,sort_solutions_seconds,total_seconds" > "$CSV_FILE"
fi


total_time=0

for case_study_spec in "${CASE_STUDY_SPECS[@]}"; do
    base_name="$(basename "$case_study_spec" .tlsf)"
    case_out_dir="$OUT_DIR/$base_name"
    mkdir -p "$case_out_dir"
    log_file="$case_out_dir/log.txt"
    if [[ -f "$log_file" ]]; then
        rm -f "$log_file"
    fi
    echo "Running repairs for case study: $case_study_spec"

    for ((run_index=1; run_index<=N_RUNS; run_index++)); do
        case_iter_dir="$case_out_dir/$run_index"
        mkdir -p "$case_iter_dir"

        SECONDS=0

        start_seconds=$SECONDS
        ./scripts/unreal-repair.sh "${FLAGS[@]}" "-out=$case_iter_dir" "${REFERENCE[@]}" "$FACTORS" "$case_study_spec" >> "$log_file" 2>&1
        unreal_repair_seconds=$((SECONDS - start_seconds))

        start_seconds=$SECONDS
        ./scripts/sort-solutions.sh -d="$case_iter_dir" -out="$case_iter_dir/maximal-specs.txt" >> "$log_file" 2>&1
        sort_solutions_seconds=$((SECONDS - start_seconds))

        # remove_non_maximal_specs "$case_iter_dir"

        echo "${case_study_spec},${run_index},${unreal_repair_seconds},${sort_solutions_seconds},$SECONDS" >> "$CSV_FILE"

        total_time=$((total_time + SECONDS))

        echo "  Run $run_index/$N_RUNS completed in $SECONDS seconds"
    done
done

echo "Total time for all runs: $total_time seconds"
