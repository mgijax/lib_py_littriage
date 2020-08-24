#!/usr/bin/env python3

# Name: getTextFromPdf.py
# Purpose: Extract the text from a PDF and write it to stdout.
#          Knows how to get text from a PDF in our pdf storage (by MGI ID).
#          Use this for a quick test.

import sys
import os
import os.path
import re
import argparse
import PdfParser
import Pdfpath

PDFDIRS = "/data/littriage"             # base directory for PDF file storage

LITPARSER = "/usr/local/mgi/live/mgiutils/litparser"        # default
if 'LITPARSER' in os.environ:
    LITPARSER = os.environ['LITPARSER']

#-----------------------------------

def getArgs():
    parser = argparse.ArgumentParser( \
        description='extract text from a PDF using litparser')

    parser.add_argument('pdf', action='store',
        help="path to PDF or MGI:nnnnnn (to pull from pdf storage)")

    parser.add_argument('--path', dest='justPath', action='store_true',
            required=False,
            help="just output path to pdf in pdf storage (instead of text)")

    args = parser.parse_args()

    return args
#-----------------------------------

args = getArgs()

## initialize litparser
PdfParser.setLitParserDir(LITPARSER)

## if we have an MGI ID, find its pdfFile in the PDF storage
MGIID_RE = re.compile(r'MGI:[0-9]+$', re.IGNORECASE)
if MGIID_RE.match(args.pdf):
    mgiID = args.pdf
    prefix, numeric = mgiID.split(':')
    dir = Pdfpath.getPdfpath(PDFDIRS, mgiID)      # get PDF storage path
    pdfFile = os.path.join(dir, numeric + '.pdf')
    if args.justPath:
        print(pdfFile)
        exit(0)
else:
    pdfFile = args.pdf

# get text from the pdf
parser = PdfParser.PdfParser(os.path.abspath(pdfFile))
textFromPdf = parser.getText()
err = parser.getStderr()
if err:
    sys.stderr.write("Stderr from %s:\n" % LITPARSER)
    sys.stderr.write(err)

sys.stdout.write(textFromPdf)
