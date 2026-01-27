#!/bin/bash

set -euo pipefail

cd "$(dirname "$0")/.." || exit 1

if ! ant compile
then
    echo "Build failed"
    exit 1
fi

profile=0
args=()
for arg in "$@"; do
    if [ "$arg" = "--profile" ]; then
        profile=1
    else
        args+=("$arg")
    fi
done

agent_opts=()
if [ $profile -eq 1 ]; then
    agent_opts=("-agentpath:${HOME}/Downloads/async-profiler-4.2.1-linux-x64/lib/libasyncProfiler.so=start,event=cpu,file=profile.html")
fi

java \
    -Xmx8g \
    -Djava.library.path=/usr/local/lib \
    -cp "bin:lib/commons-math3-3.6.1.jar:lib/rltlconv.jar:lib/JFLAP-7.0_With_Source.jar:lib/owl-18.10-snapshot.jar:lib/ejml/ejml-core-0.34.jar:lib/ejml/ejml-cdense-0.34.jar:lib/ejml/ejml-ddense-0.34.jar:lib/ejml/ejml-fdense-0.34.jar:lib/ejml/ejml-simple-0.34.jar:lib/ejml/ejml-zdense-0.34.jar:lib/ejml/ejml-dsparse-0.34.jar:lib/ejml/ejml-experimental-0.34.jar:lib/ltl2buchi.jar" \
    "${agent_opts[@]}" \
    main.SortSolutions \
    "${args[@]}"
