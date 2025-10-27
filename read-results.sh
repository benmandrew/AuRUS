#!/bin/bash

printf "%10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s\n" "" "Total" "" "" "Genuine" "" "" "Weaker" "" "" "Stronger"
printf "%10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s\n" "time(s)" "#Sol" "BestFit" "AvgFit" "#Sol" "BestFit" "AvgFit" "#Sol" "BestFit" "AvgFit" "#Sol" "BestFit" "AvgFit"

FOLDERS=("$1"/*)
for folder in "${FOLDERS[@]}"; do
    file=$folder/out.txt

    GAtime=$(grep '^Time:' "$file" | grep -o ....$)
    Sol=$(grep "Num. of Solutions: " "$file" | grep -o ....$)
    BestFit=$(grep "Best fitness:" "$file" | grep -o ....$)
    AvgFit=$(grep "AVG fitness:" "$file" | grep -o ....$)
    printf "%10s %10s %10s %10s " "${GAtime}" "${Sol}" "${BestFit}" "${AvgFit}"

    GenSol=$(grep "Genuine Solutions:" "$file" | grep -o ....$)
    GenBestFit=$(grep "Best Genuine fitness:" "$file" | grep -o ....$)
    GenAvgFit=$(grep "AVG Genuine fitness:" "$file" | grep -o ....$)
    printf "%10s %10s %10s " "${GenSol}" "${GenBestFit}" "${GenAvgFit}"

    WSol=$(grep "Weaker Solutions:" "$file" | grep -o ....$)
    WBestFit=$(grep "Best Weaker fitness:" "$file" | grep -o ....$)
    WAvgFit=$(grep "AVG Weaker fitness:" "$file" | grep -o ....$)
    printf "%10s %10s %10s " "${WSol}" "${WBestFit}" "${WAvgFit}"

    SSol=$(grep "Stronger Solutions:" "$file" | grep -o ....$)
    SBestFit=$(grep "Best Stronger fitness:" "$file" | grep -o ....$)
    SAvgFit=$(grep "AVG Stronger fitness:" "$file" | grep -o ....$)
    printf "%10s %10s %10s\n" "${SSol}" "${SBestFit}" "${SAvgFit}"
done
