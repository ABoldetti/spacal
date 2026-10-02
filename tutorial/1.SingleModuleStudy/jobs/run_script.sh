#!/bin/bash

#parse input, they are written in args.txt

COMMAND=$1
TEMPLATE=$2
OUTPUT=$3
GPS=$4
SEED=$5
set --

# do the mc
$COMMAND $TEMPLATE $OUTPUT $GPS $SEED

