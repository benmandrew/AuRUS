#!/bin/bash

set -e

TotalSol=0
TotalWOrigSol=0
TotalWSol=0
TotalGSol=0
TotalRatio=0
TotalTime=0
NRuns=0

FOLDERS=("$1"/*)
for folder in "${FOLDERS[@]}"; do
    file=$folder/out.txt
    # GAtime=$(grep '^Time:' "$file" | grep -o ....$)
    Sol=$(grep "Num. of Solutions: " "$file" | grep -o ....$)
    WOrigSol=$(grep "Num. of Solutions weaker than original:" "$file" | grep -o ...$ | sed 's/[^0-9]*//g')
    # GenSol=$(grep "Genuine Solutions:" "$file" | grep -o ....$)
    WSol=$(grep "Weaker Solutions:" "$file" | grep -o ....$)
    GSol=$(grep "Genuine Solutions:" "$file" | grep -o ....$)
    # SSol=$(grep "Stronger Solutions:" "$file" | grep -o ....$)
    Ratio=$(bc -l<<<"${WOrigSol}/${Sol}")
    Time=$(grep '^Time:' "$file" | grep -o ....$)
    TotalSol=$((TotalSol + Sol))
    TotalWOrigSol=$((TotalWOrigSol + WOrigSol))
    TotalWSol=$((TotalWSol + WSol))
    TotalGSol=$((TotalGSol + GSol))
    TotalRatio=$(bc -l<<<"${TotalRatio} + ${Ratio}")
    TotalTime=$((TotalTime + Time))
    NRuns=$((NRuns + 1))
done

AvgSol=$((TotalSol / NRuns))
AvgWOrigSol=$((TotalWOrigSol / NRuns))
AvgWSol=$((TotalWSol / NRuns))
AvgGSol=$((TotalGSol / NRuns))
NRunsFloat=$(bc -l<<<"${NRuns}")
AvgRatio=$(bc -l<<<"scale=2; ${TotalRatio}/${NRunsFloat}")
AvgTime=$((TotalTime / NRuns))

SolStandardDev=0
WOrigSolStandardDev=0
WSolStandardDev=0
GSolStandardDev=0
RatioStandardDev=0
TimeStandardDev=0
for folder in "${FOLDERS[@]}"; do
    file=$folder/out.txt
    Sol=$(grep "Num. of Solutions: " "$file" | grep -o ....$)
    Diff=$((Sol - AvgSol))
    SqDiff=$((Diff * Diff))
    SolStandardDev=$((SolStandardDev + SqDiff))
    WOrigSol=$(grep "Num. of Solutions weaker than original:" "$file" | grep -o ...$ | sed 's/[^0-9]*//g')
    Diff=$((WOrigSol - AvgWOrigSol))
    SqDiff=$((Diff * Diff))
    WOrigSolStandardDev=$((WOrigSolStandardDev + SqDiff))
    WSol=$(grep "Weaker Solutions:" "$file" | grep -o ....$)
    Diff=$((WSol - AvgWSol))
    SqDiff=$((Diff * Diff))
    WSolStandardDev=$((WSolStandardDev + SqDiff))
    GSol=$(grep "Genuine Solutions:" "$file" | grep -o ....$)
    Diff=$((GSol - AvgGSol))
    SqDiff=$((Diff * Diff))
    GSolStandardDev=$((GSolStandardDev + SqDiff))
    Ratio=$(bc -l<<<"${WOrigSol}/${Sol}")
    Diff=$(bc -l<<<"${Ratio} - ${AvgRatio}")
    SqDiff=$(bc -l<<<"${Diff} * ${Diff}")
    RatioStandardDev=$(bc -l<<<"${RatioStandardDev} + ${SqDiff}")
    Time=$(grep '^Time:' "$file" | grep -o ....$)
    Diff=$((Time - AvgTime))
    SqDiff=$((Diff * Diff))
    TimeStandardDev=$((TimeStandardDev + SqDiff))
done

SolStandardDev=$(bc -l<<<"scale=2; sqrt(${SolStandardDev}/${NRunsFloat})")
WOrigSolStandardDev=$(bc -l<<<"scale=2; sqrt(${WOrigSolStandardDev}/${NRunsFloat})")
WSolStandardDev=$(bc -l<<<"scale=2; sqrt(${WSolStandardDev}/${NRunsFloat})")
GSolStandardDev=$(bc -l<<<"scale=2; sqrt(${GSolStandardDev}/${NRunsFloat})")
RatioStandardDev=$(bc -l<<<"scale=4; sqrt(${RatioStandardDev}/${NRunsFloat})")
TimeStandardDev=$(bc -l<<<"scale=2; sqrt(${TimeStandardDev}/${NRunsFloat})")

# printf "Average total #Sol: %s (StdDev: %s)\n" "${AvgSol}" "${SolStandardDev}"
# printf "Average weaker than original #Sol: %s (StdDev: %s)\n" "${AvgWOrigSol}" "${WOrigSolStandardDev}"
# printf "Average weaker than original ratio: %s (StdDev: %s)\n" "${AvgRatio}" "${RatioStandardDev}"
# printf "Average weaker than genuine #Sol: %s (StdDev: %s)\n" "${AvgWSol}" "${WSolStandardDev}"
# printf "Average genuine #Sol: %s (StdDev: %s)\n" "${AvgGSol}" "${GSolStandardDev}"

printf "%s (%s), %s (%s), %s (%s), %s (%s), %s (%s), %s (%s)\n" \
    "${AvgSol}" "${SolStandardDev}" \
    "${AvgWOrigSol}" "${WOrigSolStandardDev}" \
    "${AvgRatio}" "${RatioStandardDev}" \
    "${AvgWSol}" "${WSolStandardDev}" \
    "${AvgGSol}" "${GSolStandardDev}" \
    "${AvgTime}" "${TimeStandardDev}"
