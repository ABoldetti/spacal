#!/bin/bash


if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <input_dir>"
    exit 1
fi

INPUT_DIR=$1
INITIAL_DIR=$(pwd)


cd $INPUT_DIR
for energy in $(find . -maxdepth 1 -type d -name "*GeV"); do
cd $energy
/home/bobolde/coding/spacal/data_analysis/scripts/root_merge.sh merge_Chi.root $INPUT_DIR/$energy "chi*"
/home/bobolde/coding/spacal/data_analysis/scripts/root_merge.sh merge_Groupd.root $INPUT_DIR/$energy "OutGroupd*"
/home/bobolde/coding/spacal/data_analysis/scripts/root_merge.sh merge_Trigd.root $INPUT_DIR/$energy "OutTrigd*"
cd ..
done
cd $INITIAL_DIR