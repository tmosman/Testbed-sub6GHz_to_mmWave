#!/bin/bash

function help { pushd .; cd eder_files_py3.8; python eder.py -h; popd; }

go_rundir="cd eder_files_py3.8"
python_cmd="python eder.py"
other_opt=""
while [[ $# > 0 ]];
do
    case "$1" in
      -h|--help)        help; read -n 1 -s; exit;;
      -g|--gui)         go_rundir="cd eder_files_py3.8/pythonGUI"; python_cmd="python viewNotebook.py"; shift;; 
      -f=*|--fref=*)    other_opt=${other_opt}" -f ${1#*=}"; shift;;
      -f|--fref)        shift; other_opt=${other_opt}" -f ${1}"; shift;;
      -r=*|--rfm=*)     other_opt=${other_opt}" -r ${1#*=}"; shift;;
      -r|--rfm)         shift; other_opt=${other_opt}" -r ${1}"; shift;;
      -u=*|--unit=*)    other_opt=${other_opt}" -u ${1#*=}"; shift;;
      -u|--unit)        shift; other_opt=${other_opt}" -u ${1}"; shift;;
      -b=*|--board=*)   other_opt=${other_opt}" -b ${1#*=}"; shift;;
      -b|--board)       shift; other_opt=${other_opt}" -b ${1}"; shift;;
      *)                other_opt=${other_opt}" -u ${1}"; shift;;
  esac
done


{
sudo modprobe -r ftdi_sio
} &> /dev/null


export LD_LIBRARY_PATH=/usr/local/lib
$go_rundir
echo $python_cmd$other_opt
#echo $other_opt
$python_cmd$other_opt
