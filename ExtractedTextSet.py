#!/usr/bin/env python3
"""
Name:  ExtractedTextSet.py
Purpose:
    This module provides utilities for recovering the extracted text for 
    references (bib_refs records) in the database.

    Extracted text is stored in the bib_workflow_data table in the database,
    but it is stored split into sections (body, references, supplemental, ...),
    and it is not so easy to recover the full text concatenated back together.

    The ExtractedTextSet class defined here does this for you.

    Convenience functions for building an ExtractedTextSet for a set of
    _refs_keys are also provided.

    If run as a script, take _ref_key as a command line argument and write
    the (full) extracted text for the reference to stdout.
    See ExtractedTextSet.py -h
"""
import argparse

def getExtractedTextSet(db,             # an initialized db module
                        refKeyList,     # list of _ref_keys
    ):
    """
    Return an ExtractedTextSet for the references with the specified keys.
    Assumes refKeyList is small enough to format into a select statement.
    Example:
        import ExtractedTextSet
        import db
        db.set_sqlServer("bhmgidevdb01")
        db.set_sqlDatabase("prod")
        db.set_sqlUser("mgd_public")
        db.set_sqlPassword("mgdpub")
        refKeys = [390554, 390545]

        ets = ExtractedTextSet.getExtractedTextSet(db, refKeys)
        for r in refKeys:
            text = ets.getExtText(r)
            ...
    """
    query = '''
        select bd._refs_key, t.term "text_type", bd.extractedtext "text_part"
        from bib_workflow_data bd join voc_term t on
                            (bd._extractedtext_key = t._term_key)
        where bd._refs_key in ( %s )
        ''' % ','.join([ str(r) for r in refKeyList ])
    results = db.sql([query], 'auto')
    ets = ExtractedTextSet(results[-1])
    return ets
#-----------------------------------

def getExtractedTextSetForTable(db,             # an initialized db module
                                tmpTableName,   # (string) name of tmp table
    ):
    """
    Return an ExtractedTextSet for the references represented in a tmpTable
        in the database.
    The only requirement for the tmpTable is that it has a _refs_key field
    (ideally, it should have an index on this field too for efficiency)
    """
    query = '''
        select r._refs_key, t.term "text_type", bd.extractedtext "text_part"
        from %s r join bib_workflow_data bd on (r._refs_key = bd._refs_key)
            join voc_term t on (bd._extractedtext_key = t._term_key)
        ''' % tmpTableName
    results = db.sql([query], 'auto')
    ets = ExtractedTextSet(results[-1])
    return ets
#-----------------------------------

class ExtractedTextSet (object):
    """
    IS	a collection of extracted text records (from multiple references)
    HAS	each extracted text record is dict with fields
        {'_refs_key' : int, 'text_type': (e.g, 'body', 'references'), 
         'text_part': text} 
        The records may have other fields too that are not used here.
        The field names '_refs_key', 'text_type', 'text_part' are specifiable.
    DOES (1)collects and concatenates all the fields for a given _refs_key into
        a single text field in the correct order - thus recapitulating the 
        full extracted text.
        (2) getExtText(refKey) - get the extracted text for a given _refs_key
        (3) join a set of basic reference records to their extracted text
    """
    # from Vocab_key = 142 (Lit Triage Extracted Text Section vocab)
    # These are the expected values for the 'text_type' field.
    validTextTypes = [ 'body', 'reference',
                        'author manuscript fig legends',
                        'star methods',
                        'supplemental', ]
    #-----------------------------------

    def __init__(self,
        extTextRcds,		# list of rcds as above
        keyLabel='_refs_key',	# name of the reference key field
        typeLabel='text_type',	# name of the text type field
        textLabel='text_part',	# name of the text field
        ):
        self.keyLabel  = keyLabel
        self.typeLabel = typeLabel
        self.textLabel = textLabel
        self.extTextRcds = extTextRcds
        self._gatherExtText()
    #-----------------------------------

    def hasExtText(self, refKey ):
        """ Return True if this ExtractedTextSet has text for refKey
        """
        return str(refKey) in self.key2TextParts
    #-----------------------------------

    def getExtText(self, refKey ):
        """ Return the text for refKey (or '' if there is no text)
        """
        extTextDict = self.key2TextParts.get(str(refKey),{})

        text =  extTextDict.get('body','') + \
                extTextDict.get('reference', '') + \
                extTextDict.get('author manuscript fig legends', '') + \
                extTextDict.get('star methods', '') + \
                extTextDict.get('supplemental', '')
        return text
    #-----------------------------------

    def joinRefs2ExtText(self,
                        refRcds,
                        refKeyLabel='_refs_key',
                        extTextLabel='ext_text',
                        allowNoText=True,
        ):
        """
        Assume refRcds is a list of records { refKeyLabel : xxx, ...}
        For each record in the list, add a field: extTextLabel: text 
            so that the extracted text becomes part of the record.
        If allowNoText is False, then an exception is raised if a refRcd is
            found with no extracted text.
        """
        for r in refRcds:
            refKey = str(r[refKeyLabel])

            if not allowNoText and refKey not in self.key2TextParts:
                raise ValueError("No extracted text found for '%s'\n" % \
                                                                    str(refKey))
            r[extTextLabel] = self.getExtText(refKey)

        return refRcds
    #-----------------------------------

    def _gatherExtText(self, ):
        """
        Gather the extracted text sections for each _refs_key
        Return dict { _refs_key: { extratedTextType : text } }
        E.g., { '12345' : {   'body'        : 'body section text',
                            'references'  : 'ref section text',
                            'star methods': '...text...',
                            } }
        (we force all _refs_keys to strings so user can use either int or str)
        """
        resultDict = {}
        for r in self.extTextRcds:
            refKey   = str(r[self.keyLabel])
            textType = r[self.typeLabel]
            textPart = r[self.textLabel]

            if textType not in self.validTextTypes:
                raise ValueError("Invalid extracted text type: '%s'\n" % \
                                                                    textType)
            if refKey not in resultDict:
                resultDict[refKey] = {}

            resultDict[refKey][textType] = str(textPart)

        self.key2TextParts = resultDict
        return self.key2TextParts
    #-----------------------------------
# end class ExtractedTextSet -----------------------------------


#-----------------------------------
# if run as a script, write extracted text for a reference to stdout
#-----------------------------------

def getArgs():
    parser = argparse.ArgumentParser( \
        description='get extracted text for a reference and write it to stdout')

    parser.add_argument('ref_key', default=None,
        help="reference key to get extracted text for")

    parser.add_argument('-s', '--server', dest='server', action='store',
        required=False, default='dev',
        help='db server: adhoc, prod, or dev (default)')

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
#-----------------------------------

if __name__ == "__main__":
    import sys
    import db as dbModule

    args = getArgs()
    dbModule.set_sqlServer(args.host)
    dbModule.set_sqlDatabase(args.db)
    dbModule.set_sqlUser("mgd_public")
    dbModule.set_sqlPassword("mgdpub")

    ets = getExtractedTextSet(dbModule, [args.ref_key])
    text = ets.getExtText(args.ref_key)
    print(text)
