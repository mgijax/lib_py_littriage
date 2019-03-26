#!/usr/bin/env python2.7

#
#  Purpose: split extracted text files into sections:
#		body, references, manuscript figs, star methods, supp data
#		output "|" delimited text file summarizing results
#	    This provides a way to pull all these section predictions into a
#               spreadsheet to analyze in bulk.
#
#  Input:
#	directories that contain extracted text files.
#	Assumes:
#	Directory names are journal names.
#	Files within directories are extracted text files named by pubmed ID
#	See bulkGetExtText.py
#
#  Outputs:
#    Write to stdout.
#    For each extracted text file, write one line with columns defined below
#
###########################################################################
import sys
import os
import string
import time
import re
import argparse
import extractedTextSplitter as sp

#-----------------------------------

def getArgs():
    parser = argparse.ArgumentParser( \
	description= \
	'''
	Split extracted text from a bunch of files
	To stdout, write one line per file describing the split
	''')

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
        required=False, help="messages to stderr")

    parser.add_argument('dirNames', nargs=argparse.REMAINDER,
	help= \
	'''
	directory names holding text files to split.
	Typically these files would be named by PubMed ID.
	''')

    args =  parser.parse_args()

    return args
###################################

FD = '|'	# output field delimiter

outputCols = [ "ID",
		"Doc_len",		# extracted text length
		"Ref_reason",		# reason refs section was predicted
		"Ref_sPos",		# start position in ext text of refs
		"Ref_len",		# length of refs section
		"Mfig_reason",
		"Mfig_sPos",
		"Mfig_len",
		"%_body",		# percent of doc Refs+Mfig are
					#  w/ star methods & supp data removed
		"Star_reason",
		"Star_sPos",
		"Star_len",
		"Supp_reason",
		"Supp_sPos",
		"Supp_len",
		"Only_refs",		# 1/0 "mice" only in reference section
		"Journal", 
	    ]

miceRegex = re.compile( r'\bmice\b', flags=re.IGNORECASE)

splitter = sp.ExtTextSplitter()
numRefMiceOnly = 0		# num of papers with "mice" only in refs
# ----------------------------------
def main():
    global numRefMiceOnly

    args = getArgs()
    startTime = time.time()

    sys.stdout.write( FD.join(outputCols) + '\n')	# output header
    numProcessed = 0
    for dn in args.dirNames:

	# directories are journal names
	if dn.endswith(os.sep): 		# path ends in '/'
	    journal = dn.split(os.sep)[-2]	# last part of the dir path
	else:
	    journal = dn.split(os.sep)[-1]	# last part of the dir path

	# file names are pubmed IDs
	for fn in os.listdir(dn):

	    numProcessed += 1
	    if args.verbose and numProcessed % 1000 == 0: # progress indicator
		sys.stderr.write("..%d" % numProcessed)

	    pubmedID = os.path.splitext(fn)[0]	# filename w/o any extension
	    pn       = os.sep.join([dn, fn])	# pathname to open

	    fp = open(pn, 'r')
	    text = fp.read()
	    fp.close()

	    process_one_document(text, journal, pubmedID)
    # finish
    sys.stderr.write("\n%d articles have 'mice' only in Refs section\n"  \
				    % numRefMiceOnly)
    sys.stderr.write("%d files analyzed. Elapsed time: %8.2f seconds\n\n" \
				    % (numProcessed, time.time() - startTime) )
# ----------------------------------

def process_one_document(text, journal, pubmedID):
    global sp
    global numRefMiceOnly
    # Section objects
    textLength = len(text)
    (bodyS, refsS, manuS, starS, suppS) = splitter.findSections(text)

    miceRefsOnly = isMiceRefsOnly(bodyS, refsS, manuS, starS, suppS)
    numRefMiceOnly += miceRefsOnly

    # calc the percent of the length used to compare to maxFraction
    ref_manuLength = starS.sPos - refsS.sPos	# len of refs + manuFig
    ref_manuPercent = 100.0 * float(ref_manuLength)/float(starS.sPos)

    outputLineParts =     [ "%s" % pubmedID]
    outputLineParts.append( "%d" % textLength )

    outputLineParts.append( refsS.reason.replace('\n',' ').strip() )
    outputLineParts.append( "%d" % refsS.sPos )
    outputLineParts.append( "%d" % (refsS.ePos - refsS.sPos) )

    outputLineParts.append( manuS.reason.replace('\n',' ').strip() )
    outputLineParts.append( "%d" % manuS.sPos )
    outputLineParts.append( "%d" % (manuS.ePos - manuS.sPos) )

    outputLineParts.append( "%4.1f" % ref_manuPercent )

    outputLineParts.append( starS.reason.replace('\n',' ').strip() )
    outputLineParts.append( "%d" % starS.sPos )
    outputLineParts.append( "%d" % (starS.ePos - starS.sPos) )

    outputLineParts.append( suppS.reason.replace('\n',' ').strip() )
    outputLineParts.append( "%d" % suppS.sPos )
    outputLineParts.append( "%d" % (suppS.ePos - suppS.sPos) )

    outputLineParts.append( "%d" % miceRefsOnly )
    outputLineParts.append( journal )

    sys.stdout.write( FD.join(outputLineParts) + '\n')
# ----------------------------------

def isMiceRefsOnly(bodyS, refsS, manuS, starS, suppS):
    """ Return True if "mice" only occurs in the reference section (refsS)
    """
    numMiceRefs  = len( miceRegex.findall(refsS.text) )
    numMiceOther = len( miceRegex.findall(  \
		    bodyS.text + manuS.text + starS.text + suppS.text) )
    return (numMiceOther == 0) and (numMiceRefs > 0)

# ----------------------------------
#
#  MAIN
#
if __name__ == "__main__": main()
