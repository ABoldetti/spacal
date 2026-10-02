#source /cvmfs/sft.cern.ch/lcg/views/LCG_105/x86_64-el9-gcc13-opt/setup.sh

SIMPATH="$SPACAL"
CONFIG="base.cfg"
BASEFOLDEROUT="out"
BASEFOLDERJOB='jobs'
ZN='200' 
EMIN='1.5'
EMAX='2.7'
EN='24'
PRIMARIES='100'
JOBS='5'
QUEUE='workday'

python3 ${SIMPATH}/parametrization/prepareOpticalCalibration.py \
--build ${SIMPATH}/build \
--config ${CONFIG} \
--baseFolderOut ${BASEFOLDEROUT} \
--baseFolderJobs ${BASEFOLDERJOB} \
--zn ${ZN} \
--emin ${EMIN} \
--emax ${EMAX} \
--en ${EN} \
--primaries ${PRIMARIES} \
--jobs ${JOBS} \
--local \
--queue ${QUEUE} 
