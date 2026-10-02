#!/bin/bash

for i in 1.0GeV 2.0GeV 5.0GeV 10.0GeV 20.0GeV 40.0GeV 60.0GeV 80.0GeV 100.0GeV 
do
  cd /afs/cern.ch/work/a/aboldett/simulations/slanted_e2/jobs/$i
  condor_submit jobs.sub
  cd - 
done
