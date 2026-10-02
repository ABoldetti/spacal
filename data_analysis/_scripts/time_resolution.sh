#!/bin/bash
# ./data_analysis/_scripts/time_resolution.sh compacted_data/slanted_e data_analysis/time_resolution/slanted_e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <input dir> <output dir>"
    exit 1
fi

INPUT_DIR="$1"
OUTPUT_DIR="$2"
INITIAL_DIR=$(pwd)

for dir in $(ls $INPUT_DIR |grep GeV); do
    echo "Processing directory:$dir --------------------------------------------------------------------------------------------------------------------"
    for energy in $(ls $dir); do
    mkdir -p $OUTPUT_DIR/$energy
        echo "Processing energy: $energy--------------------------------------------------------------------------------------------------------------------"
        for i in $(ls $dir/$energy | grep Groupd); do
            echo "$INPUT_DIR/$energy/$i" "$OUTPUT_DIR/$energy/$i"
            python3 data_analysis/_scripts/time_resolution.py "$INPUT_DIR/$energy/$i" "$OUTPUT_DIR/$energy/$i" "root_resolution/$(basename $INPUT_DIR)" 
        done
    done
done
cd $INITIAL_DIR



python3 /home/bobolde/coding/spacal/data_analysis/_scripts/energy_convertion.py "data_analysis/readout/$(basename $INPUT_DIR)" "root_resolution/$(basename $INPUT_DIR)"


