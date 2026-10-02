#!/usr/bin/python3
# -*- coding: utf-8 -*-

import math
import os
import stat
import sys
import argparse
import subprocess
from subprocess import Popen, PIPE, STDOUT
import threading
import time
import multiprocessing

def worker(path,line,count):
  
  comm = '/home/bobolde/coding/spacal/tutorial/1.SingleModuleStudy/jobs/run_script.sh'
  cmd = [comm]
  for i in line.split():
    cmd.append(i)
  # print(cmd)
  logName = '/home/bobolde/coding/spacal/tutorial/1.SingleModuleStudy/jobs/log/log_' + str(count) +  '.log'
  log = open(logName, 'w')
  subprocess.Popen(cmd,stdout = log,stderr=log).wait()
  log.close()
  return

def main(argv):
  #parsing args
  parser = argparse.ArgumentParser(description='Python script to start jobs in parallel')
  parser.add_argument('--num' , default=-1, help='Number of PCs in the farm')
  parser.add_argument('--here', default=-1, help='Part of jobs to run on this pc')
  parser.add_argument('--cores', default=8, help='Number of cores to use')
  args = parser.parse_args()
  numberOfPCs = int(args.num)
  thisPC      = int(args.here)
  cores       = int(args.cores)
  splitJobs = False
  if numberOfPCs == -1:
    if thisPC != -1:
      print ('ERROR: if you specify --num you should specify also --here  ')
      sys.exit()
  if thisPC == -1:
    if numberOfPCs != -1:
      print ('ERROR: if you specify --num you should specify also --here  ')
      sys.exit()
  # now both -1 or both a number 
  if thisPC != -1:
    if numberOfPCs != -1:
      splitJobs = True
  pool = multiprocessing.Pool(cores) 
  # preparing 
  path = os.path.abspath('./')
  # take only 1/3 of the jobs if lineNum is specified 
  processList = []
  filepath = '/home/bobolde/coding/spacal/tutorial/1.SingleModuleStudy/jobs/args.txt'
  countLine = 0
  lines = len(open(filepath).readlines())
  limit = lines / numberOfPCs
  uplimit = limit * thisPC 
  downlimit = limit * (thisPC -1) 
  with open(filepath) as fp:
    for line in fp:
      if splitJobs == True:
        if countLine >= downlimit:
          if countLine < uplimit:
            pool.apply_async(worker, args=(path,line,countLine))
            #print(countLine)
      else:
        pool.apply_async(worker, args=(path,line,countLine))
      countLine = countLine + 1
  pool.close()
  pool.join()

if __name__ == '__main__':
  main(sys.argv[1:])
