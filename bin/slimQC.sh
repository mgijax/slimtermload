#!/bin/sh
#
#  vaQC.sh
###########################################################################
#
#  Purpose:
#
#      This script is a wrapper around the process that does QC
#      checks for the  vocabulary abbreviation load
#
#  Usage:
#
#      vaQC.sh  configfile filename  
#
#      where
#          filename = full path to the input file
#
#  Env Vars:
#
#      See the configuration file
#
#  Inputs:
#	VA input file
#
#  Outputs:
#
#      - QC report for the input file.
#
#      - Log file (${QC_LOGFILE})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal initialization error occurred
#      2:  Invalid obo version
#      3:  QC errors
#
#  Assumes:  Nothing
#
#  Implementation:
#
#      This script will perform following steps:
#
#      ) Validate the arguments to the script.
#      ) Validate & source the configuration files to establish the environment.
#      ) Verify that the input file exists.
#      ) Initialize the log and report files.
#      ) Call vaQC.py to generate the QC report.
#
#  Notes:  None
#
###########################################################################
#
#  Modification History:
#
#  Date        SE   Change Description
#  ----------  ---  -------------------------------------------------------
#
#  07/2/2014  sc  Initial development
#
###########################################################################
CURRENTDIR=`pwd`
BINDIR=`dirname $0`

USAGE='Usage: vaQC.sh  configfile filename'

# this is a QC check only run, set LIVE_RUN accordingly
LIVE_RUN=0; export LIVE_RUN

#
# Make sure an input file was passed to the script. If the optional "live"
# argument is given, that means that the output files are located in the
# /data/loads/... directory, not in the current directory.
#
CONFIG_COMMON=`cd ${BINDIR}/..; pwd`/va_common.config
. ${CONFIG_COMMON}

echo "$1 $2"
if [ $# -eq 2 ]
then
    CONFIG=`cd ${BINDIR}/..; pwd`/$1
    #echo "CONFIG=${CONFIG}"
    INPUT_FILE=$2
elif [ $# -eq 3 -a "$3" = "live" ]
then
    CONFIG=`cd ${BINDIR}/..; pwd`/$1
    echo "CONFIG=${CONFIG}"
    INPUT_FILE=$2
    LIVE_RUN=1
else
    echo ${USAGE}; exit 1
fi
#
# Make sure the configuration file exists and source it.
#
if [ -f ${CONFIG} ]
then
    . ${CONFIG}
else
    echo "Missing configuration file: ${CONFIG}"
    exit 1
fi


#
# If this is not a "live" run, the output, log and report files should reside
# in the current directory, so override the default settings.
#
if [ ${LIVE_RUN} -eq 0 ]
then
	QC_RPT=${CURRENTDIR}/`basename ${QC_RPT}`
	QC_LOGFILE=${CURRENTDIR}/`basename ${QC_LOGFILE}`

fi
#
# Make sure the input file exists (regular file or symbolic link).
#
if [ "`ls -L ${INPUT_FILE} 2>/dev/null`" = "" ]
then
    echo "Missing input file: ${INPUT_FILE}"
    exit 1
fi

#
# Initialize the log file.
#
LOG=${QC_LOGFILE}
rm -rf ${LOG}
touch ${LOG}

#
# Initialize the report files to make sure the current user can write to them.
#
rm -f ${QC_RPT}; >${QC_RPT}

#
# Run qc checks on the input file
#
echo "" >> ${LOG}
date >> ${LOG}
echo "Run QC checks on the input file" >> ${LOG}

${VALOAD_QC}  ${INPUT_FILE}
STAT=$?
if [ ${STAT} -eq 1 ]
then
    echo "Fatal initialization error. See ${QC_RPT}" | tee -a ${LOG}
    echo "" | tee -a ${LOG}
    exit ${STAT}
fi

if [ ${STAT} -eq 2 ]
then
    echo "QC errors detected. See ${QC_RPT}" | tee -a ${LOG}
    echo "" | tee -a ${LOG}
else
    echo "No QC errors detected."
fi

echo "" >> ${LOG}
date >> ${LOG}
echo "Finished running QC checks on the input file" >> ${LOG}

exit 0
