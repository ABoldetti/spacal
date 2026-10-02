# Script to prepare the hybrid simulation jobs 
# What follows is an example based on a personl AFS and EOS structure. Adapt it to your needs, according 
# to this structure (explained also in the README.md file):
#
# prepareChain.py                 <needs to be prepareChain.py, hence modify the path>
# --config                        <full path of module configuration file>
# --baseFolderJobs                <name of subfolder of current folder where the condor job scripts will 
#                                  be prepared (will be created by the prepareChain.py script)> 
# --baseFolderOut                 <base folder for the simulation output files>
# --build                         <your folder where the HybridMC executables are located>
# --pulse                         <use this flag to enable the pulse formation part - no args required>
# --pulseConfig                   <signal formation config file>
# --baseGPS                       <base GPS file, defining particle type, beam shape and direction>
# --events                        <how many primary events to simulate in total, for each energy>
# --listCalibrations              <list of optical calibrations files, one per module type>
#                                 <calibration files are just separated by space, and they need >
#                                 <to match the module numbers given in the --listTypes key>
#                                 <HOWEVER in a single module type, --listTypes can be omitted>
#                                 <        and a single calibration file can be given here>
# --listEnergy                    <list of primary particle energies to be simulated, in GeV>
# --listEvents                    <For each energy point (in the same order of --listEnergy>
#                                 <how many events will be simulated in a single job>
# --listQueue                     <For each energy point (in the same order of --listEnergy>
#                                 <the HTCondor queue for the corresponding jobs>
#
# By default, the simulation will KEEP in eos the output files of the Geant4 simulation step, 
# containing the energy deposition and Cherenkov data. It will DISCARD the hybrid output,
# i.e. the huge files with the list of all optical photons exiting the module, it will 
# DISCARD the pulse shapes files (the OutGroupBy* files) and will of course KEEP the 
# final pulse formation files, with photoelectrons and timestamp information (the OutTrigd* files).
# If you want to modify this, consider using the flags 
# --discardEnergyDepositions
# --keepHybrid
# --keepGroupBy
# whose names should be self explanatory. 
# 
# Remeber to scale the --listEvents and --listQueue properly, so that your jobs are not killed. 
# Run some short test jobs to get an idea of the parameters to use

# source /cvmfs/sft.cern.ch/lcg/views/LCG_97python3/x86_64-centos7-gcc9-opt/setup.sh

python3 $SPACAL/parametrization/prepareChain.py \
--listEnergy 1 2 5 10 20 40 60 80 100 \
--listEvents 250 250 100 50 20 10 10 5 5 \
--listQueue workday workday workday workday workday workday workday workday workday \
--baseFolderJobs jobs \
--build $SPACAL/build/ \
--pulse \
--chi \
--keepGroupBy \
--discardEnergyDepositions \
--pulseConfig SignalConfigFile_HPKR7600U-20_CFD04.cfg \
--events 1000 \
--config spacal_one_side_PbPoly_1.5mm_fibres.cfg \
--baseGPS gps_e.mac \
--baseFolderOut /eos/user/a/aboldett/simulations/slanted_e2 \
--listCalibrations calibration_100_2000_10.data
