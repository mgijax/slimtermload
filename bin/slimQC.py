#!/usr/local/bin/python
#
#  slimQC.py
###########################################################################
#
#  Purpose:
#
#	This script will generate a QC report for the slim term file
#
#  Usage:
#
#      slimQC.py  filename
#
#      where:
#          filename = path to the input file
#
#  Env Vars:
#
#      The following environment variables are set by the configuration
#      files that are sourced by the wrapper script:
#
#          QC_RPT
#	   
#  Inputs:
# 	vocabulary abbreviation input file
#	Columns:
#	1. termID
#	2. term
#	3. abbreviation (optional)
#
#  Outputs:
#
#      - QC report (${QC_RPT})
#
#  Exit Codes:
#
#      0:  Successful completion
#      1:  Fatal initialization error occurred
#      2:  QC errors detected in the input files
#
#  Assumes:
#
#  Implementation:
#
#      This script will perform following steps:
#
#      1) Validate the arguments to the script.
#      2) Perform initialization steps.
#      3) Run the QC checks.
#      4) Create update.sql file if no QC errors
#      5) Close input/output files.
#
#  Notes:  None
#
###########################################################################

import sys
import os
import string
import re
import mgi_utils
import db

db.setAutoTranslate(False)
db.setAutoTranslateBE(False)

#
#  CONSTANTS
#
TAB = '\t'
CRT = '\n'

USAGE = 'Usage: slimQC.py  inputFile'

#
#  GLOBALS
#

# Report file name
qcRptFile = os.environ['QC_RPT']

# lines from the input where ID is not in the database
invalidIDList = []

# lines in the input where term for ID in the input does not match i
# term for ID in the database
invalidTermList = []

# list of rows with < 3 columns
invalidRowList = []

# lines in the input whose terms are obsolete in the database
obsoleteTermList = []

# vocabulary we are adding abbreviations to
vocabKey = os.environ['VOCAB_KEY']
print vocabKey
# term ID lookup {termId:term, ...}
termIdLookup = {}

# 1 if QC errors
hasQcErrors = 0

class Term:
    # Is: data object for term info (VOC_Term)
    # Has: a set of term attributes
    # Does: provides direct access to its attributes
    #
    def __init__ (self):
        # Purpose: constructor
        # Returns: nothing
        # Assumes: nothing
        # Effects: nothing
        # Throws: nothing
        self.term = None
        self.ID = None
        self.isObsolete = None
	self.termKey = None

#
# Purpose: Validate the arguments to the script.
# Returns: Nothing
# Assumes: Nothing
# Effects: sets global variable
# Throws: Nothing
#
def checkArgs ():
    global inputFile

    if len(sys.argv) != 2:
        print USAGE
        sys.exit(1)

    inputFile = sys.argv[1]

    return


#
# Purpose: Perform initialization steps.
# Returns: Nothing
# Assumes: Nothing
# Effects: opens files
# Throws: Nothing
#
def init ():
    openFiles()
    
    # load lookups
    results = db.sql('''select a.accid, t.term, t.isObsolete, t._Term_key
	from ACC_Accession a, VOC_Term t
	where t._Vocab_key = %s
	and t._Term_key = a._Object_key
	and a._MGIType_key = 13''' % vocabKey, 'auto')

    for r in results:
	id = r['accid']
	t = Term()
	t.term = r['term']
	t.ID = id
	t.isObsolete = r['isObsolete']
	t.termKey = r['_Term_key']
	termIdLookup[id] = t

    return


#
# Purpose: Open input and output files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Sets global variables.
# Throws: Nothing
#
def openFiles ():
    global fpInfile, fpQcRpt

    #
    # Open the input file.
    #
    try:
        fpInfile = open(inputFile, 'r')
    except:
        print 'Cannot open input file: %s' % inputFile
        sys.exit(1)

    try:
        fpQcRpt = open(qcRptFile, 'w')
    except:
        print 'Cannot open report file: %s' % qcRptFile
        sys.exit(1)

    return
#
# Purpose: run the QC checks
# Returns: Nothing
# Assumes: Nothing
# Effects: sets global variables, write report to file system
# Throws: Nothing
#
def runQcChecks ():

    global hasQcErrors

    #
    # parse the obo file into a data structure
    #
    lineCt = 0
    for line in fpInfile.readlines():
	lineCt += 1
        tokens = string.split(line, TAB)

	# now strip line for reporting purposes
	line = string.strip(line)
	#print tokens
	#print 'len tokens: %s' % len(tokens)
	if len(tokens) < 3:
	    hasQcErrors = 1
	    invalidRowList.append('%s: %s%s' % (lineCt, line, CRT))
	    continue
	# abbrev can be blank, so don't strip until after tokenization or
	# a QC error will be reported for <3 columns
        termId = string.strip(tokens[0])
	term = string.strip(tokens[1])
	abbrev = string.strip(tokens[2])
	if termId == '' or term == '':
	    hasQcErrors = 1
            invalidRowList.append('%s: %s%s' % (lineCt, line, CRT))
        if not termIdLookup.has_key(termId):
	    hasQcErrors = 1
	    invalidIDList.append('%s: %s%s' % (lineCt, line, CRT))
	else:
	    termObject =  termIdLookup[termId]
	    dbTerm = termObject.term
	    dbTermKey = termObject.termKey
	    if dbTerm != term:
		hasQcErrors = 1
		invalidTermList.append('%s: %s dbTerm: "%s"%s' % (lineCt, line, dbTerm, CRT))
	    if termObject.isObsolete:
		hasQcErrors = 1
		obsoleteTermList.append('%s: %s%s' % (lineCt, line, CRT))
    if hasQcErrors:
	if len(invalidRowList):
	    fpQcRpt.write('\nInput lines with missing data or < 3 columns:\n')
	    fpQcRpt.write('-----------------------------\n')
	    for line in invalidRowList:
		fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(invalidIDList):
	    fpQcRpt.write('\nInput lines with invalid IDs:\n')
            fpQcRpt.write('------------------------\n') 
	    for line in invalidIDList:
                fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(invalidTermList):
	    fpQcRpt.write('\nInput lines where term does not match the ID in the database:\n')
            fpQcRpt.write('-------------------------------------------------------------\n')
            for line in invalidTermList:
                fpQcRpt.write(line)
	    fpQcRpt.write('\n')
	if len(obsoleteTermList):
	    fpQcRpt.write('\nInput lines where term is obsolete in the database:\n')
            fpQcRpt.write('---------------------------------------------------\n')
            for line in obsoleteTermList:
                fpQcRpt.write(line)
    return
	
#
# Purpose: Close the files.
# Returns: Nothing
# Assumes: Nothing
# Effects: Nothing
# Throws: Nothing
#
def closeFiles ():
    global fpInfile, fpQcRpt
    fpInfile.close()
    fpQcRpt.close()
    return

#
# Main
#
checkArgs()
init()
runQcChecks()
closeFiles()
if hasQcErrors == 1 : 
    sys.exit(2)
else:
    sys.exit(0)
