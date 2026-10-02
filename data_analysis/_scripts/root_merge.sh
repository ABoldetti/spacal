#!/bin/bash

# Script: merge_OutGroupd.sh
# Purpose: Merge multiple OutGroupd files into a single output file.

# Usage: ./merge_OutGroupd.sh <output_file> <input_file1> <input_file2> ...

if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <output_file> <input_dir> <name characteristics>"
    exit 1
fi

OUTPUT_FILE="$1"
INPUT_DIR="$2"
NAME=$3
INITIAL_DIR=$(pwd)

cd $INPUT_DIR
hadd ../$OUTPUT_FILE $(find -maxdepth 1 -name "$NAME")

mv ../$OUTPUT_FILE ./$OUTPUT_FILE

cd $INITIAL_DIR

