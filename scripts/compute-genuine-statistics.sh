#!/bin/bash

set -euo pipefail

ant compile > /dev/null

REFERENCES=(-ref=case-studies/minepump/genuine/minepump_fixed0.tlsf -ref=case-studies/minepump/genuine/minepump_fixed1.tlsf -ref=case-studies/minepump/genuine/minepump_fixed2.tlsf)
SOLUTIONS_DIR=result-backup/minepump/1

output=$(java -Xmx8g -Djava.library.path=/usr/local/lib \
    -cp "bin:lib/commons-math3-3.6.1.jar:lib/rltlconv.jar:lib/JFLAP-7.0_With_Source.jar:lib/owl-18.10-snapshot.jar:lib/ejml/ejml-core-0.34.jar:lib/ejml/ejml-cdense-0.34.jar:lib/ejml/ejml-ddense-0.34.jar:lib/ejml/ejml-fdense-0.34.jar:lib/ejml/ejml-simple-0.34.jar:lib/ejml/ejml-zdense-0.34.jar:lib/ejml/ejml-dsparse-0.34.jar:lib/ejml/ejml-experimental-0.34.jar:lib/ltl2buchi.jar" \
    main.GenuineSolutionsMinimal \
    "${REFERENCES[@]}" "$SOLUTIONS_DIR")

echo "$output" | jq .
