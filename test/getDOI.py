#!/usr/bin/env python3

# Name: getDOI.py
# Purpose: Extract the DOI ID for the specified paper and write it to stdout
#          Use this for a quick test.

USAGE = """
Usage:  getDOI.py [litparser directory] pdffile or MGIID
"""

import sys
import os
import os.path
import re
import PdfParser
import Pdfpath

PDFDIRS = "/data/littriage"             # base directory for PDF file storage

LITPARSER = "/usr/local/mgi/live/mgiutils/litparser"        # default
if 'LITPARSER' in os.environ:
    LITPARSER = os.environ['LITPARSER']

if len(sys.argv) == 3:
    LITPARSER = os.path.abspath(sys.argv[1])
    pdfFile = sys.argv[2]
elif len(sys.argv) == 2 and not sys.argv[1].startswith('-'):
    pdfFile = sys.argv[1]
else:
    sys.stderr.write(USAGE)
    sys.exit(5)

## initialize litparser
PdfParser.setLitParserDir(LITPARSER)

## if we have an MGI ID, find its pdfFile in the PDF storage
MGIID_RE = re.compile(r'MGI:[0-9]+$', re.IGNORECASE)
if MGIID_RE.match(pdfFile):
    mgiID = pdfFile
    prefix, numeric = mgiID.split(':')
    dir = Pdfpath.getPdfpath(PDFDIRS, mgiID)      # get PDF storage path
    pdfFile = os.path.join(dir, numeric + '.pdf')
    sys.stdout.write('File: %s\n' % pdfFile)

## Try to get the DOI ID
parser = PdfParser.PdfParser(os.path.abspath(pdfFile))
id = parser.getFirstDoiID()
if id == None:
    sys.stdout.write('Could not find doi ID\n')
    sys.exit(5)
else:
    sys.stdout.write(id + '\n')
