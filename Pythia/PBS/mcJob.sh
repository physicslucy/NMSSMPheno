#!/bin/bash
#
# This is a generic script for running a Pythia8 job on PBS.
# Used in submit_mc_jobs_pbs.py
# Usage:
#   qsub <PBS options> -v exe="generateMC.exe",args="<program options>" mcJob.sh
#
#
# Default PBS settings:
#PBS -l walltime=5:00:00
#PBS -l mem=50mb
#PBS -l nodes=1:ppn=1
#
# Setup modules
# module load null python gcc/4.9.1 boost numpy/1.9.1 cmake gsl
# module unload intel
# env | grep PBS

# cd $HOME/NMSSMPheno/Pythia
eval "${exe} ${args}"