#!/bin/bash

#parse input, they are written in args.txt

COMMAND=$1
TEMPLATE=$2
OUTPUT=$3
GPS=$4
PROPAGATE=$5
CALIBRATION=$6
HYBRID=$7
SEED=$8
FLUX=$9
PULSEGROUPBY=${10}
PULSETR=${11}
PULSECONFIG=${12}
OUTGROUPBY=${13}
OUTTR=${14}
CALCULATECHI=${15}
OUTCHI=${16}
CALCULATEENRES=${17}
OUTENRES=${18}
JUSTOUT=${19}
set --

source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh
# do the MC
$COMMAND $TEMPLATE output_temp $GPS $SEED 

# do the hybrid propagation
$PROPAGATE -i output_temp.root -c "$CALIBRATION" -o hybrid_temp.root --photonSeed $SEED --type 0  --rebinCali 1 

### Do the GroupBy
$PULSEGROUPBY -c $PULSECONFIG -i hybrid_temp.root -o output_f1

### Do the pulse triggering
$PULSETR -c $PULSECONFIG -i output_f1.root -o output_f2 
### Do the chi calculation
$CALCULATECHI -e output_temp.root -p output_f2.root -o chi_temp.root 
echo "Copying GroupBy file..."

xrdcp --nopbar output_f1.root root://eosuser.cern.ch/$OUTGROUPBY.root

echo "Copying Trigger file..."

xrdcp --nopbar output_f2.root root://eosuser.cern.ch/$OUTTR.root

echo "Copying chi file..."

xrdcp --nopbar chi_temp.root root://eosuser.cern.ch/$OUTCHI.root

