#!/usr/local/bin/python

# Name: getDOI.py
# Purpose: Extract the DOI ID for the specified paper and write it to stdout
#          Use this for a quick test.

USAGE = """
Usage:  getDOI.py [litparser directory] pdffile
"""

import sys
import os
import os.path
import PdfParser

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

PdfParser.setLitParserDir(LITPARSER)

parser = PdfParser.PdfParser(os.path.abspath(pdfFile))
id = parser.getFirstDoiID()
if id == None:
    sys.stdout.write('Could not find doi ID\n')
    sys.exit(5)
else:
    sys.stdout.write(id + '\n')
