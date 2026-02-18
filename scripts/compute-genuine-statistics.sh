#!/bin/bash

set -euo pipefail

ant compile > /dev/null

run_case_study() {
    local references_dir="$1"
    local solutions_dir="$2"

    local references=()
    for f in "$references_dir"/*.tlsf; do
        references+=("-ref=$f")
    done

    local output
    output=$(java -Xmx8g -Djava.library.path=/usr/local/lib \
        -cp "bin:lib/commons-math3-3.6.1.jar:lib/rltlconv.jar:lib/JFLAP-7.0_With_Source.jar:lib/owl-18.10-snapshot.jar:lib/ejml/ejml-core-0.34.jar:lib/ejml/ejml-cdense-0.34.jar:lib/ejml/ejml-ddense-0.34.jar:lib/ejml/ejml-fdense-0.34.jar:lib/ejml/ejml-simple-0.34.jar:lib/ejml/ejml-zdense-0.34.jar:lib/ejml/ejml-dsparse-0.34.jar:lib/ejml/ejml-experimental-0.34.jar:lib/ltl2buchi.jar" \
        main.GenuineSolutionsMinimal \
        "${references[@]}" "$solutions_dir")

    echo "$output" | jq -r '[.n_total_solutions,.n_genuine_solutions,.n_weaker_solutions,.n_stronger_solutions] | @csv'
}

RESULTS_DIR="result/GyroUnrealizable_Var1_710_GyroAspect_unrealizable"
if [ ! -d "$RESULTS_DIR" ]; then
    echo "Results directory $RESULTS_DIR does not exist."
    exit 1
fi

GENUINE_SOLUTIONS_DIR="case-studies/GyroUnrealizable_Var1/genuine"
if [ ! -d "$GENUINE_SOLUTIONS_DIR" ]; then
    echo "Genuine solutions directory $GENUINE_SOLUTIONS_DIR does not exist."
    exit 1
fi

OUTPUT_CSV="analysis-results/genuine/GyroUnrealizable_Var1.csv"
if [ -f "$OUTPUT_CSV" ]; then
    echo "Output CSV $OUTPUT_CSV already exists. Please remove it before running the script."
    exit 1
fi

tmpdir=$(mktemp -d)
trap 'rm -rf "$tmpdir"' EXIT

N_JOBS=${N_JOBS:-4}
i=0

echo "n_total_solutions,n_genuine_solutions,n_weaker_solutions,n_stronger_solutions" > "$OUTPUT_CSV"

for result in "$RESULTS_DIR"/*; do
    while [ "$(jobs -pr | wc -l)" -ge "$N_JOBS" ]; do
        wait -n
    done
    i=$((i+1))
    run_case_study "$GENUINE_SOLUTIONS_DIR" "$result" > "$tmpdir/$i.csv" &
done

wait

for f in "$tmpdir"/*.csv; do
    cat "$f" >> "$OUTPUT_CSV"
done
