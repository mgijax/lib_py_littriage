"""
Name: doiRetry.py

Purpose: run DoiFinder on extracted text on papers already in the db and see
    how well it finds the correct DOI ID by comparing it to each ref's official
    DOI ID in the accession table.
    This is a way to do a comprehensive test of the DoiFinder
    
Process:
1. do a query to select some references (see command line options)
    This populates a tmp table in the database:
        tmp_refs:  _refs_key, MGI ID, DOI ID, Journal, creation_date, year

2. for those references
    get their extracted text from db & run the DoiFinder,
        compare w/ their official ID
    OR
    get their pdf, extract text, & run the DoiFinder,  <--- tests pdftotext too
        compare w/ their official ID

    before we run the DoiFinder, we can
        * (not implemented) see if DOI ID is in the 1st 30 chars, and if so,
            remove it (this was likely manually added to the PDF)
        * see if the "MGI Supplemental Data" tag is in the text, and if so,
            remove it and everything after it

        then we can see how the DOI finding works on what would be the original
        paper
"""

###########################################################################
import sys
import os
import time
import traceback
import argparse
import re
import db
import ExtractedTextSet
import PdfParser
import Pdfpath

#-----------------------------------

def getArgs():
    parser = argparse.ArgumentParser( \
        description='test DoiFinder on refs already in the db.')

# JIM add options for:
#  doi ID prefix
#  remove DOI ID if found in 1st n chars

    parser.add_argument('--test', dest='test', action='store_true',
        required=False, help="just run ad hoc test code to test this script")

    parser.add_argument('--start', dest='startDate', action='store',
        required=False, default='2020-01-01',
        help='start date, default=2020-01-01')

    parser.add_argument('--end', dest='endDate', action='store',
        required=False, default='2020-07-31',
        help='end date, default=2020-07-31')

    parser.add_argument('--journal', dest='journal', action='store',
        required=False, default=None, help='journal name')

    parser.add_argument('--ids', dest='mgiIDs', action='store',
        required=False, default=None,
        help='MGI ID list, e.g., "MGI:6383486,MGI:6415924"')

    parser.add_argument('-y', '--year', dest='year', action='store',
        required=False, default=None, type=int, help='publication year')

    parser.add_argument('-l', '--limit', dest='limit', action='store',
        required=False, default=100, type=int,
        help='How many refs to return. Default 100. Use 0 for no limit.')

    parser.add_argument('--pdf', dest='fromPDFs', action='store_true',
        required=False, default=False, help='pull text from PDFs')

    parser.add_argument('--fromDB', dest='fromPDFs', action='store_false',
        required=False, default=False,
        help='pull text from extracted text in db (default)')

    parser.add_argument('-s', '--server', dest='server', action='store',
        required=False, default='dev',
        help='db server: prod, or dev (default)')

    parser.add_argument('-v', '--verbose', dest='verbose', action='store_true',
        required=False, help="include helpful messages to stderr")

    args =  parser.parse_args()

    if args.server == 'prod':
        args.host = 'bhmgidb01'
        args.db = 'prod'
    if args.server == 'dev':
        args.host = 'bhmgidevdb01'
        args.db = 'prod'

    return args
###################################

args = getArgs()

db.set_sqlServer  ( args.host)
db.set_sqlDatabase( args.db)
db.set_sqlUser    ("mgd_public")
db.set_sqlPassword("mgdpub")

SQLSEPARATOR = '||'
BUILD_REF_TMP_TABLE = [ \
'''
    create temporary table tmp_refs
    as
    select r._refs_key, a.accid doi, a2.accid mgiid, r.year, r.journal,
        to_char(r.creation_date, 'YYYY/MM/DD') as "r_creation_date"
        --to_char(r.modification_date, 'YYYY/MM/DD') as "r_modification_date",
        --to_char(bd.modification_date, 'YYYY/MM/DD') as "bd_modification_date"
    from bib_refs r join bib_workflow_data bd on
            (r._refs_key = bd._refs_key and bd._extractedtext_key = 48804490)
                                                        -- this is "body"
         join acc_accession a on
            (a._object_key = r._refs_key and a._logicaldb_key=65 -- doi
            and a._mgitype_key=1 )
         join acc_accession a2 on
            (a2._object_key = r._refs_key and a2._logicaldb_key=1 -- mgi
            and a2._mgitype_key=1 and a2.prefixpart='MGI:' )
    where
    bd.haspdf=1
    and bd.extractedtext is not Null        -- ensure we're finding refs w/
    and length(bd.extractedtext) > 200      --    valid extracted text
    --and r.creation_date >= '2020-01-01'
    --and a2.accid = 'MGI:6442050'
''',    # where clauses added below based on cmd line options
'''
    create index tmp_idx1 on tmp_refs(_refs_key)
''',
'''
    create index tmp_idx2 on tmp_refs(r_creation_date)
''',
]
BUILD_REF_TMP_TABLE[0] += "and r.creation_date >= '%s'\n" % args.startDate
BUILD_REF_TMP_TABLE[0] += "and r.creation_date <= '%s'\n" % args.endDate

if args.year:
    BUILD_REF_TMP_TABLE[0] += "and r.year = %s\n" % args.year

if args.journal:
    BUILD_REF_TMP_TABLE[0] += "and r.journal = '%s'\n" % args.journal

if args.mgiIDs:
    idList = [ "'%s'" % i.strip().upper() for i in args.mgiIDs.split(',') ]
    idList = ','.join(idList)
    BUILD_REF_TMP_TABLE[0] += "and a2.accid in (%s)\n" % idList

if args.limit:
    BUILD_REF_TMP_TABLE[0] += "limit %d\n" % args.limit

def main ():
    verbose( "Hitting database %s %s as mgd_public\n\n" % (args.host, args.db))
    startTime = time.time()

    db.sql(BUILD_REF_TMP_TABLE, 'auto')
    QUERY = "select * from tmp_refs"
    results = db.sql(QUERY.split(SQLSEPARATOR), 'auto')

    endTime = time.time()
    verbose("Total SQL time: %8.3f seconds\n\n" % (endTime-startTime))

    eth = ExtTextHandler(args.fromPDFs)
    doiFinder = PdfParser.DoiFinder()

    exceptsFound, noneFound, wrongFound, correctFound = 0,0,0,0
    exceptionOutput = ''

    header = '\t'.join(['doiStatus',
                        'mgiID',
                        'creation_date',
                        'extText_len',
                        'journal',
                        'doiID',
                        'foundDoiID',
                        '1st doi pos',
            ])
    print(header)

    for i,r in enumerate(results[-1]):
        refs_key      = str(r['_refs_key'])
        doiID         = r['doi']
        mgiID         = r['mgiid']
        year          = str(r['year'])
        r_creation_date = r['r_creation_date']
        journal       = r['journal']

        if i % 50 == 0: verbose("%d..." % i)

        try:            # Get the text
            extText       = eth.getExtText(r)
        except Exception as e:
            exceptionOutput += "exception while extracting text on %s\n" % mgiID
            (t, v, tb) = sys.exc_info()
            exceptionOutput += ''.join(traceback.format_tb(tb))
            exceptionOutput += str(e) + '\n'
            exceptsFound += 1
            continue

        extText = cleanText(extText)

        try:            # Find the DOI
            foundDoiID    = doiFinder.getDoiID(extText)
        except Exception as e:
            exceptionOutput += "exception getting doiID on %s\n" % mgiID
            (t, v, tb) = sys.exc_info()
            exceptionOutput += ''.join(traceback.format_tb(tb))
            exceptionOutput += str(e) + '\n'
            exceptsFound += 1
            continue

        if not foundDoiID:
            doiStatus = "none found"
            foundDoiID = "none"
            noneFound += 1
            charPos = -1
        elif foundDoiID != doiID:
            doiStatus = "wrong doi"
            wrongFound += 1
            charPos = extText.find(doiID)
        else:
            doiStatus = "correct doi"
            correctFound += 1
            charPos = extText.find(doiID)

        line = '\t'.join([doiStatus,
                            mgiID,
                            r_creation_date,
                            str(len(extText)),
                            journal,
                            doiID,
                            foundDoiID,
                            str(charPos),
                ])
        print(line)

    print('')
    print(exceptionOutput)
    print("Exceptions: %d" % exceptsFound)
    print("Refs w/ no      DOI found: %d" % noneFound)
    print("Refs w/ wrong   DOI found: %d" % wrongFound)
    print("Refs w/ correct DOI found: %d" % correctFound)
    print("%d total refs" % (exceptsFound+noneFound+wrongFound + correctFound))

    endTime = time.time()
    verbose("Total runtime: %8.3f seconds\n\n" % (endTime-startTime))

# end main() ----------------------------------

SUPP_DATA_TAG = 'MGI Lit Triage Supplemental Data'
def cleanText(t):
    i = t.find(SUPP_DATA_TAG)
    if i == -1:
        return t
    else:
        return t[:i]
# end cleanText() ----------------------------------

class ExtTextHandler (object):
    """
    IS: knows how to get the extracted text for a reference record, either
        from the database or from our PDF storage
    DOES:  getExtText(self, reference_record)
    """
    def __init__(self, fromPDFs):
        if not fromPDFs:
            verbose("getting extracted text from the db...\n")
            self.ets = ExtractedTextSet.getExtractedTextSetForTable(db, \
                                                                'tmp_refs')
            verbose("...done\n")
        else:
            self.ets = None
            self.PDFDIRS = '/data/littriage'   # base dir for PDF file storage

            self.LITPARSER = "/usr/local/mgi/live/mgiutils/litparser" # default
            if 'LITPARSER' in os.environ:
                self.LITPARSER = os.environ['LITPARSER']

            PdfParser.setLitParserDir(self.LITPARSER)

    def getExtText(self, r):
        """
        Get extracted text, either from the db or the PDF.
        r is a record with keys: '_refs_key'  or 'mgiid'
        Return None if for some reason we can't get the text.
        """
        if self.ets:            # from database
            refsKey = r['_refs_key']
            if self.ets.hasExtText(refsKey):
                t = self.ets.getExtText(refsKey)
            else:
                t = None
        else:                   # from pdf file in our pdf storage
            mgiID = r['mgiid']
            prefix, numeric = mgiID.split(':')
            dirName = Pdfpath.getPdfpath(self.PDFDIRS, mgiID)
            pdfFile = os.path.join(dirName, numeric + '.pdf')
            parser = PdfParser.PdfParser(os.path.abspath(pdfFile))
            t = parser.getText()
        return t
# end class ExtTextHandler ----------------------------------

def verbose(text):
    if args.verbose:
        sys.stderr.write(text)
        sys.stderr.flush()

if __name__ == "__main__":
    if not (len(sys.argv) > 1 and sys.argv[1] == '--test'):
        main()
        exit()

    if True:    # ad hoc tests
        pass
