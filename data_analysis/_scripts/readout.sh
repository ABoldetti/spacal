#!/bin/bash


if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <calibration_file> <data_directory>"
    exit 1
fi

CALIB_PATH="$1"
DATA_DIR="$2"
INITIAL_DIR=$(pwd)
for dir in $DATA_DIR; do
    mkdir -p "$INITIAL_DIR/data_analysis/readout/$(basename $dir)"
    echo "Processing directory:$(basename $dir) $dir--------------------------------------------------------------------------------------------------------------------"
    sleep 5
    for i in $(ls $dir); do
        $SPACAL/build/readout -f "$dir/$i" -o "$INITIAL_DIR/data_analysis/readout/$(basename $dir)/$i.root" -c $CALIB_PATH -n 5 -t 1
    done
done
cd $INITIAL_DIR

