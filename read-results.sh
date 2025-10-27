#!/bin/bash

printf "%10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s\n" "" "Total" "" "" "Genuine" "" "" "Weaker" "" "" "Stronger"
printf "%10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s\n" "time(s)" "#Sol" "BestFit" "AvgFit" "#Sol" "BestFit" "AvgFit" "#Sol" "BestFit" "AvgFit" "#Sol" "BestFit" "AvgFit"

for K in {1..10}
do
DIR=$1_$K
file=$DIR/out.txt

GAtime=$(grep '^Time:' $file | grep -o ....$)
#Sol=$(ls -1q $DIR/spec* | wc -l)
Sol=$(grep "Num. of Solutions: " $file | grep -o ....$)
BestFit=$(grep "Best fitness:" $file | grep -o ....$)
AvgFit=$(grep "AVG fitness:" $file | grep -o ....$)

#GenSol=$(grep "Genuine Solutions:" $file | awk -F"," '{print NF-1}')
GenSol=$(grep "Genuine Solutions:" $file | grep -o ....$)
GenBestFit=$(grep "Best Genuine fitness:" $file | grep -o ....$)
GenAvgFit=$(grep "AVG Genuine fitness:" $file | grep -o ....$)

#WSol=$(grep "Weaker Solutions found" $file | awk -F"," '{print NF-1}')
WSol=$(grep "Weaker Solutions:" $file | grep -o ....$)
WBestFit=$(grep "Best Weaker fitness:" $file | grep -o ....$)
WAvgFit=$(grep "AVG Weaker fitness:" $file | grep -o ....$)

#SSol=$(grep "Stronger Solutions found" $file | awk -F"," '{print NF-1}')
SSol=$(grep "Stronger Solutions:" $file | grep -o ....$)
SBestFit=$(grep "Best Stronger fitness:" $file | grep -o ....$)
SAvgFit=$(grep "AVG Stronger fitness:" $file | grep -o ....$)

printf "%10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s %10s\n" "${GAtime}" "${Sol}" "${BestFit}" "${AvgFit}" "${GenSol}" "${GenBestFit}" "${GenAvgFit}" "${WSol}" "${WBestFit}" "${WAvgFit}" "${SSol}" "${SBestFit}" "${SAvgFit}"

done
