'''
#
# Pdfpath.py
#
# Purpose: provide PDF/path functions
#
# To call from littriageload:
#	import Pdfpath
#	pdfpath = Pdfpath.getPdfpath('/data/littriage', 'MGI:1095183')
#
# To test from command line ((output will be sent to standard out)
#	python Pdfpath.py
#
# History
#
# 07/06/2017	lec
#	- TR12250/Lit Triage
#
'''

import sys
import os

PROJECT_DIR_GROUPING = 1000

#
# Purpose:  return PDF file path based on the numeric part of the MGI:xxxx
#
def getPdfpath(parentpath, mgiID):

    prefix, numeric = mgiID.split(':')
    basepath = (int(numeric) / PROJECT_DIR_GROUPING) * PROJECT_DIR_GROUPING
    return str(parentpath) + '/' + str(basepath)

if __name__ == '__main__':

    print 'MGI:1095183'
    print getPdfpath('/data/littriage', 'MGI:1095183')
    print ''

    print 'MGI:1195539'
    print getPdfpath('/data/littriage', 'MGI:1195539')
    print ''

    print 'MGI:3758969'
    print getPdfpath('/data/littriage', 'MGI:3758969')
    print ''
