#!/bin/bash

set -euo pipefail

ant compile > /dev/null

run_case_study() {
    local references_dir="$1"
    local solutions_dir="$2"

    local references=()
    for f in "$references_dir"/*.tlsf; do
        references+=("--ref=$f")
    done

    local output
    output=$(java -Xmx8g -Djava.library.path=/usr/local/lib \
        -cp "bin:lib/commons-math3-3.6.1.jar:lib/rltlconv.jar:lib/JFLAP-7.0_With_Source.jar:lib/owl-18.10-snapshot.jar:lib/ejml/ejml-core-0.34.jar:lib/ejml/ejml-cdense-0.34.jar:lib/ejml/ejml-ddense-0.34.jar:lib/ejml/ejml-fdense-0.34.jar:lib/ejml/ejml-simple-0.34.jar:lib/ejml/ejml-zdense-0.34.jar:lib/ejml/ejml-dsparse-0.34.jar:lib/ejml/ejml-experimental-0.34.jar:lib/ltl2buchi.jar" \
        main.GenuineSolutionsMinimal \
        --n-solutions \
        "${references[@]}" "$solutions_dir")

    echo "$output" | jq -r '[.n_total_solutions,.n_genuine_solutions,.n_weaker_solutions,.n_stronger_solutions] | @csv'
}

RESULTS_DIR="result-av3/arbiter"
if [ ! -d "$RESULTS_DIR" ]; then
    echo "Results directory $RESULTS_DIR does not exist."
    exit 1
fi

GENUINE_SOLUTIONS_DIR="case-studies/arbiter/genuine"
if [ ! -d "$GENUINE_SOLUTIONS_DIR" ]; then
    echo "Genuine solutions directory $GENUINE_SOLUTIONS_DIR does not exist."
    exit 1
fi

for result in "$RESULTS_DIR"/*/; do
    echo "Processing result: $result"
    run_case_study "$GENUINE_SOLUTIONS_DIR" "${result%/}"
done
