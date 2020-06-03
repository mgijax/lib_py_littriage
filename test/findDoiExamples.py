#!/usr/bin/env python2.7

#
#  Purpose: Find example references for different flavors of DOI handling
#             so we can build a set of test cases.
#
#  Outputs: Reference IDs and snippets from their extracted text that appear
#             to be DOI IDs. This way you can browse the different ways
#             the DOI IDs are formated.
#
###########################################################################
import sys
import os
import string
import time
import argparse
import re
import db

#-----------------------------------

def getArgs():
    parser = argparse.ArgumentParser( \
        description='find DOI IDs in extracted text for refs with a given prefix')

    parser.add_argument('doiPrefix', default=None,
        help="doi ID prefix to find references for. E.g., 10.1177")

    parser.add_argument('-y', '--year', dest='year', action='store',
        required=False, default=None, type=int,
        help='publication year')

    parser.add_argument('-l', '--limit', dest='limit', action='store',
        required=False, default=100, type=int,
        help='SQL limit. How many refs to return. Default is 100')

    parser.add_argument('-s', '--server', dest='server', action='store',
        required=False, default='dev',
        help='db server: adhoc, prod, or dev (default)')

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
        required=False, help="include helpful messages to stderr")

    args =  parser.parse_args()

    if args.server == 'adhoc':
	args.host = 'mgi-adhoc.jax.org'
	args.db = 'mgd'
    if args.server == 'prod':
	args.host = 'bhmgidb01'
	args.db = 'prod'
    if args.server == 'dev':
	args.host = 'bhmgidevdb01'
	args.db = 'prod'

    return args
###################################

args = getArgs()

SQLSEPARATOR = '||'
QUERY =  \
'''
select a.accid doi, a2.accid pubmed, r.year, r.journal, bd.extractedtext
from bib_refs r join bib_workflow_data bd on
            (r._refs_key = bd._refs_key and bd._extractedtext_key = 48804490)
     join acc_accession a on
	 (a._object_key = r._refs_key and a._logicaldb_key=65 -- doi
	  and a._mgitype_key=1 )
     join acc_accession a2 on
	 (a2._object_key = r._refs_key and a2._logicaldb_key=29 -- pubmed
	  and a2._mgitype_key=1 )
where
bd.haspdf=1
and bd.extractedtext is not Null        -- ensure we're finding refs w/
and length(bd.extractedtext) > 200      --    valid extracted text
and a.accid like '%s%%'
''' % args.doiPrefix

if args.year:
    QUERY += "and r.year = %s\n" % args.year

QUERY += "limit %d\n" % args.limit


regex = args.doiPrefix.replace('.', r'\.')      # escape any '.'s
doi_re = re.compile(regex)

def main ():
    db.set_sqlServer  ( args.host)
    db.set_sqlDatabase( args.db)
    db.set_sqlUser    ("mgd_public")
    db.set_sqlPassword("mgdpub")

    verbose( "Hitting database %s %s as mgd_public\n\n" % (args.host, args.db))

    queries = string.split(QUERY, SQLSEPARATOR)

    startTime = time.time()
    results = db.sql( queries, 'auto')
    endTime = time.time()
    verbose( "Total SQL time: %8.3f seconds\n\n" % (endTime-startTime))

    for i,r in enumerate(results[-1]):
        doi     = r['doi']
        pubmed  = r['pubmed']
        year    = r['year']
	journal = r['journal']
        extText = r['extractedtext']
        print('\nArticle %s %s %s %s:' % (pubmed, doi, year, journal, ))
        for j,m in enumerate(doi_re.finditer(extText)): # 1st few id occurrances
            pos = m.start()
            print("ID %d: '%s'" % (j, extText[pos:pos+31]))
            if j > 3: break

# end main() ----------------------------------

def verbose(text):
    if args.verbose:
        sys.stderr.write(text)
        sys.stderr.flush()

if __name__ == "__main__":
    main()
