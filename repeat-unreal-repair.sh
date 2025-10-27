#!/bin/bash

FACTORS="-factors=0.7,0.1,0.1,0.1"
FLAGS=(-Max=1000 -Gen=1000 -Pop=100 -k=20 -GATO=7200 -addA)
REFERENCE=(-ref=case-studies/arbiter/genuine/arbiter_fixed0.tlsf -ref=case-studies/arbiter/genuine/arbiter_fixed1.tlsf -ref=case-studies/arbiter/genuine/arbiter_fixed2.tlsf -ref=case-studies/arbiter/genuine/arbiter_fixed3.tlsf)

for i in $(seq 1 10);
do
    OUT=-out=result/arbiter/run_$i
    ./unreal-repair.sh "${FLAGS[@]}" "$OUT" "${REFERENCE[@]}" "$FACTORS" case-studies/arbiter/arbiter.tlsf
done
