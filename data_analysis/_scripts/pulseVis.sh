#!/bin/bash


if [ "$#" -eq 0 ] || [ "$#" -gt 2 ]; then
    echo "Usage: $0  <data_directory> <output_directory>"
    exit 1
fi

if [ "$#" -eq 1 ]; then
    DATA_DIR="$1"
    OUT_DIR="pulseVis"
fi

if [ "$#" -eq 2 ]; then
    DATA_DIR="$1"
    OUT_DIR="$2"
fi
INITIAL_DIR=$(pwd)

mkdir -p $OUT_DIR
for i in $(ls $DATA_DIR); do
    for name in $(ls $DATA_DIR/$i/ | grep Groupd); do

        mkdir -p "$INITIAL_DIR/$OUT_DIR/$(basename $i)"
        root -l -b -q '/home/bobolde/coding/spacal/data_analysis/scripts/edit_pulseVisualization.C("'${name%.root}'" , "'$DATA_DIR/$(basename $i)'" , "'$OUT_DIR/$(basename $i)'")'
    done
    
done
/home/bobolde/coding/spacal/data_analysis/scripts/removeDict.sh