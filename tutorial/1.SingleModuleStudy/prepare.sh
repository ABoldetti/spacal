#!/bin/bash

#########################################
# Hybrid MC - Single Module Simulation  #
#########################################
#### Small script to prepare a Single Module Simulation 
#### This one is already prepared a WGAGG module simulation
#### but can be adapted to any use case
####
#### This script prepares simulations for 3 different platforms
#### and 3 different simulation modalities. 
#### Possible platforms are:
#### 1) Locally on your PC  --> local
#### 2) On LXPLUS           --> lxplus
#### 3) On the grid         --> grid
#### Possible simulation modalities are
#### 1) Particle gun        --> pgun
#### 2) Flux                --> flux
#### So for example, if you want to run it locally a particle gun simulation, the sintax is
####
#### ./prepare.sh local pgun
####
#### Before running, you will need to modify some variables in this script to 
#### adapt to your configuration. In particular, read Section 1. to 
#### understand the meaning of the variables, then modify Sections 2. and 3.


#########################################
# ATTENTION!                            #
#########################################
# On lxplus, DO NOT run this from a EOS folder! copy the script to one of your AFS folders, modify and run.
#########################################


#########################################
# WHAT YOU NEED TO DO                   #
#########################################
#### In a nutshell, the MINIMAL things to do are:
#### 1) Define your platform and sim modality 
#### 2) Modify SIMPATH in section 2, to the full path where you downloaded the gitlab code
#### 2) Modify LISTCALIBRATIONS, and FLUX in Section 2. if needed (depending on your 
####    usecase, you might want to use the same files already written here)
#### 3) Modify BASEFOLDEROUT in Section 3 if needed. If you don't, the output will go in a subfolder 'out' of current
####    folder. While this would be ok for local runs and irrelevant for grid runs, it would be a problem for lxplus runs,
####    where you probably want to store the output files in some EOS folder and not in your AFS space 
#### 4) If the other flags are already adapted to your needs, save and run this script, as explained above
####    Otherwise modify also the other flags, as explained in Section 1
#### 5) Submit the jobs running the run script produced at the end of execution
#########################################


#########################################
# SOME OPERATIONS...                    #
#########################################
### Store cmd args
PLATFORM=$1
MODALITY=$2
### Prepare some flags
PLATFORM_FLAG=''
MODALITY_FLAG=''
### Some variable declaration
SIMPATH=''
LISTCALIBRATIONS=''
FLUX=''
### Check cmd args number
if [ "$#" -ne 2 ]; then
  echo "You need to provide 2 arguments:"
  echo "./prepare.sh [local|lxplus|grid] [pgun|flux]"
  exit 1
fi
### Check cmd args values 
## PLATFORM
if [ ${PLATFORM} != "local" ] && [ ${PLATFORM} != "lxplus" ] && [ ${PLATFORM} != "grid" ]; then
  echo "Invalid argument ${PLATFORM} . Valid choices for argument 1 are [local|lxplus|grid]"
  exit 1
fi
## MODALITY
if [ ${MODALITY} != "pgun" ] && [ ${MODALITY} != "flux" ]; then
  echo "Invalid argument ${MODALITY} . Valid choices for argument 2 are [pgun|flux]"
  exit 1
fi
### Set env variables, flags etc 
### for PLATFORM (MODALITY needs to be done later)
if [ ${PLATFORM} = "local" ]; then
  PLATFORM_FLAG='--local'
else 
  if [ ${PLATFORM} = "lxplus" ]; then
    PLATFORM_FLAG=''
    source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh
  else 
    if [ ${PLATFORM} = "grid" ]; then
      PLATFORM_FLAG='--grid'
      source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh
    fi
  fi
fi
#########################################


#########################################
# SECTION 1. VARIABLES EXPLAINED        #
#########################################
#
### Files and paths: 
#
# - SIMPATH                             Path to your spacal simulation git code folder
# - BASEFOLDEROUT                       Folder where the output will be saved
# - BASEFOLDERJOB                       Folder where the job scripts will be saved
# - CONFIG                              Main module/calorimeter config file
# - PULSECONFIG                         Pulse formation config file
# - BASEGPS                             Base GPS file for pgun simulations. Ignored for flux simulations
# - FLUX                                The flux file you want to use. Ignored in pgun simulations
#
### Lists. 
## Associate module types to their calibrations. These 2 lists need to be specified in the same order, 
## the values are just separated by a space (no commas), and the lists need to have the same number of entries
#
# - LISTTYPES                           List of module types in the simulation, with the same order as LISTCALIBRATIONS
# - LISTCALIBRATIONS                    List of optical calibration files - this is already set for you, although
#                                       clearly for the 'local' condition it will not make sense for your PC
#
### Input particles:
## Except EVENTS, which is a single number, the 3 lists below need to be specified in the same order, 
## the values are just separated by a space (no commas), and the lists need to have the same number of entries
#
# - LISTENERGY                          pgun: the list of energies in GeV (of the primary particle defined in BASEGPS)
#                                             that will be shot to the module/calorimeter. e.g. LISTENERGY='1 2 3 5 10 20 35 50 100'
#                                       flux: this is just the name of the output subfolder (subfolder of BASEFOLDEROUT) 
#                                             and IT HAS to be a number, but it could be any number, it won't matter (eg: LISTENERGY='5555')
# - EVENTS                              pgun: number of primaries shot, for each energy in the above list
#                                       flux: number of flux events taken from the flux file defined in FLUX. 
#                                             Leave -1 to take all flux events 
# - LISTEVENTS                          pgun: how many primaries (of each energy) are shot per job  
#                                       flux: Leave it equal to 1 for flux simulations
# - LISTQUEUE                           List job queues on lxplus, irrelevant in local and grid jobs
#                                       See LXPLUS/HTCondor documentation for a list of options
#
### Just to clarify the last 3 flags above, an example. For a pgun simulation, if you set:
#
# LISTENERGY='1 5 10'
# EVENTS='1000'
# LISTEVENTS='200 100 50'
# LISTQUEUE='longlunch tomorrow nextweek'
#
# The script will prepare (1000/200) = 5  jobs with primary particles shot at 1 GeV, on longlunch queue
#                         (1000/100) = 10 jobs with primary particles shot at 5 GeV, on tomorrow queue
#                         (1000/50)  = 20 jobs with primary particles shot at 10 GeV, on nextweek queue
#
### Option:
# - DISK                                Facultative: on LXPLUS, irrelevant in local and grid jobs
#                                       if you need some specific amount of disk 
#                                       memory during the simulation chain  (e.g. 50GB for the hybrid 
#                                       files with Upgrade II MB) you request it here. If the default HTCondor 
#                                       disk amount is enough (20 GB), you can remove it
#########################################


#########################################
# SECTION 2. SIM CODE, CALIB. AND FLUX  #
#########################################
### Modify what you need among these 3 cases, following guidelines above. Obviously you 
### Need to modify only flag relative to your current use case
if [ ${PLATFORM} = "local" ]; then
  ### Options for local simulations. Validy for my PC, modify for yours!!!
  SIMPATH='/home/marco/cernbox/Universita/LHCb/Simulations/Spacal/'
  LISTCALIBRATIONS='/home/marco/cernbox/Universita/LHCb/Devs/TimeCutsEtc/SPACAL-W/calibration.data'
  FLUX='/home/marco/cernbox/Universita/LHCb/Devs/Test_Full_Runs/Run3/FluxGammaB2KstGamma_MB_Merged.root'
else 
  if [ ${PLATFORM} = "lxplus" ]; then
    ### Options for lxplus simulations. Valid for my lxplus, modify for yours!!!
    ### You can anyway use the same LISTCALIBRATIONS (and eventually FLUX) since 
    ### they are save on our EOS shared space
    SIMPATH='/afs/cern.ch/work/m/mpizzich/simulations/spacal/gitlab/'
    LISTCALIBRATIONS='/eos/experiment/spacal/Simulations/CalibrationLibrary/spacal_W_gfag_pitch1.67_12.12x12.12cm.cfg/calibration.data'
    FLUX='/eos/experiment/spacal/Simulations/Test_Run4_Run5_Full_ECAL/FluxGammaB2KstGamma_MB_Merged.root'
  else 
    if [ ${PLATFORM} = "grid" ]; then
      ### Options for grid simulations. Valid for my lxplus settings, modify for yours!!!
      ### You can anyway use the same LISTCALIBRATIONS since it should be available on DIRAC. 
      ### Same goes for FLUX, which is on our shared EOS space
      SIMPATH='/afs/cern.ch/work/m/mpizzich/simulations/spacal/gitlab/'
      LISTCALIBRATIONS='LFN:/lhcb/user/m/mpizzich/Run5Calibrations/spacal_W_gfag_pitch1.67_12.12x12.12cm_calibration.data'
      FLUX='/eos/experiment/spacal/Simulations/Test_Run4_Run5_Full_ECAL/FluxGammaB2KstGamma_MB_Merged.root'
    fi
  fi
fi
#########################################


#########################################
# SECTION 3. FILES, FOLDERS AND FLAGS   #
#########################################
BASEFOLDEROUT='out_full'
BASEFOLDERJOB='jobs_full'
CONFIG='base.cfg'
BASEGPS='gps_e_3+3.mac'  
PULSECONFIG='SignalConfigFile_HPKR7600U-20_FL1_CFD02.cfg'
# LISTTYPES='1 2 3 4 5 6'
LISTENERGY='1 2 5 10 20 35 50 100'
EVENTS='1000'
LISTEVENTS='50 25 20 10 5 4 2 1'
LISTQUEUE='testmatch testmatch testmatch testmatch testmatch testmatch testmatch testmatch' 
DISK='50GB'      
#
# These flags are commented because already defined in Section 2. If you
# prefer, you can comment the whole Section 2 and hardcode them here.
#SIMPATH=            
#LISTCALIBRATIONS=   
#FLUX=               
#
#########################################


#########################################
### Now we can set some flags...
if [ ${MODALITY} = "pgun" ]; then 
  MODALITY_FLAG=''
  else 
  if [ ${MODALITY} = "flux" ]; then 
    MODALITY_FLAG="--useFlux ${FLUX}"
  fi
fi 
QUEUE_FLAG=''
DISK_FLAG=''
GPS_FLAG=''
if [ "${BASEGPS}" != '' ]; then
  GPS_FLAG="--baseGPS ${BASEGPS}" 
fi
if [ ${PLATFORM} = "lxplus" ]; then
  QUEUE_FLAG="--listQueue ${LISTQUEUE}"
  if [ "${DISK}" != '' ]; then
    DISK_FLAG="--requestDisk ${DISK}"
  fi
fi
#########################################


#########################################
# THE ACTUAL PREPARE COMMAND            #
#########################################

python3 ${SIMPATH}/parametrization/prepareChain.py ${PLATFORM_FLAG} ${MODALITY_FLAG} ${QUEUE_FLAG} ${DISK_FLAG} ${GPS_FLAG} \
--config ${CONFIG} \
--pulse \
--pulseConfig ${PULSECONFIG} \
--listCalibrations ${LISTCALIBRATIONS} \
--listEvents ${LISTEVENTS} \
--build ${SIMPATH}/build \
--baseFolderOut ${BASEFOLDEROUT} \
--listEnergy ${LISTENERGY} \
--baseFolderJobs ${BASEFOLDERJOB} \
--events ${EVENTS} \
--chi \
--keepGroupBy \
--discardEnergyDepositions
#########################################