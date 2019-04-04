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
# 04/04/2019	jak
#	- TR12763
'''

import sys
import os

PROJECT_DIR_GROUPING = 1000

#
# Purpose:  return pathname to the directory for a PDF based on the numeric
#		part of the MGI:xxxx
#
def getPdfpath(parentpath, mgiID):

    try:
        prefix, numeric = mgiID.split(':')
        basepath = (int(numeric) / PROJECT_DIR_GROUPING) * PROJECT_DIR_GROUPING
        return os.path.join( str(parentpath), str(basepath) )
    except:
        raise Exception('Failed to obtain pdf path: %s, %s' % (parentpath, mgiID))

if __name__ == '__main__':

    #print 'MGI:'
    #print getPdfpath('/data/littriage', 'MGI:')
    #print ''

    print 'MGI:1'
    print getPdfpath('/data/littriage', 'MGI:1')
    print ''

    print 'MGI:11'
    print getPdfpath('/data/littriage', 'MGI:11')
    print ''

    print 'MGI:111'
    print getPdfpath('/data/littriage', 'MGI:111')
    print ''

    print 'MGI:1111'
    print getPdfpath('/data/littriage/', 'MGI:1111')
    print ''

    print 'MGI:11111'
    print getPdfpath('/data/littriage/', 'MGI:11111')
    print ''

    print 'MGI:111111'
    print getPdfpath('/data/littriage/', 'MGI:111111')
    print ''

    print 'MGI:1111111'
    print getPdfpath('/data/littriage/', 'MGI:1111111')
    print ''

