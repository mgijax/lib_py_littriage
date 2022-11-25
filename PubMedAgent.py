# Purpose: to provide an easy means to fetch reference data from PubMed in
#	a variety of formats
# Usage:
# 1. call setToolName() and/or setEmailAddress() as desired to override
#	default values
# 2. instantiate a PubMedAgent, PubMedAgentJson, or PubMedAgentMedline
#	(depending on your desired return type)
# 3. start passing DOI IDs (singly or in a list) to the agent and getting
#	back data in your desired format using getReference(doiID) or getReferences(doiList)

import csv
import xml.dom.minidom 
import os
import re
import HttpRequestGovernor

###--- Globals ---###

# name of tool making the request (sent to PubMed for tracking)
TOOL_NAME = 'PubMedAgent'

# email address in case contact is needed (sent to PubMed for tracking)
EMAIL_ADDRESS = 'mgi-help@jax.org'

# return Medline or Json format from PubMed request? (internal use)
# return type
MEDLINE = 'medline'
JSON = 'json'
XML = 'xml'

# return mode
TEXT='text'

# e-utilities key
EUTILS_API_KEY =  os.environ['EUTILS_API_KEY']

# URL for sending DOI IDs to PubMed to be converted to PubMed IDs;
# need to fill in tool name, email address, and comma-delimited list of DOI IDs
PUBMEDID_CONVERTER_URL = '''https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=%s&term=%s[lid]&api_key=''' + EUTILS_API_KEY
PMCID_CONVERTER_URL = '''https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pmc&retmode=%s&term=%s[lid]&api_key=''' + EUTILS_API_KEY

# URL for sending PubMed IDs to PubMed to get reference data for them;
# need to fill in comma-delimited list of PubMed IDs, requested return mode,
# tool name, and email address
REFERENCE_FETCH_URL = '''https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=%s&retmode=%s&rettype=%s&api_key=''' + EUTILS_API_KEY

# Governer is needed to ensure we don't issue too many requests of eutils and start getting 429 errors.
# Eutils allows 3 per second, so max out at 2 just to be conservative.
gov = HttpRequestGovernor.HttpRequestGovernor(0.5, 120, 7200, 172800)

# LID/ELOCATORE search
ELOCATOR_RE = re.compile('(E[0-9]+)')

###--- Functions ---###

def setToolName(tool):
    # Purpose: change the tool name submitted to NCBI (for their tracking purposes)

    global TOOL_NAME

    TOOL_NAME = tool
    return

def setEmailAddress(email):
    # Purpose: change email address submitted to NCBI (for their tracking purposes)
    global EMAIL_ADDRESS

    EMAIL_ADDRESS = email
    return

###--- Classes ---###

class PubMedReference:
    # Is: a Python representation of data for a single reference from 
    #	PubMed
    # Does: provides easy access within Python to reference attributes
    # Notes: if an errorMessage is provided rather than a reference record,
    #  this PubMedReference will be flagged as isValid() == False, and the
    #	error message is then accessible from getErrorMessage().

    def __init__ (self, errorMessage = None):
        self.pubMedID = None
        self.doiID = None
        self.title = None
        self.authors = None
        self.journal = None
        self.date = None
        self.year = None
        self.issue = None
        self.pages = None
        self.abstract = None
        self.volume = None
        self.primaryAuthor = None
        self.publicationType = None
        self.elocator = None
        # add other fields as needed

        self.errorMessage = errorMessage

        return

    ###--- setter/getter methods ---###

    def isValid(self):
        return self.errorMessage == None

    def getErrorMessage(self):
        return self.errorMessage
    def setPubMedID(self, pmID):
        self.pubMedID = pmID
    def getPubMedID(self):
        return self.pubMedID
    def setDoiID(self, doiID):
        self.doiID = doiID
    def getDoiID(self):
        return self.doiID
    def setTitle(self, title):
        self.title = title
    def getTitle(self):
        return self.title
    def setAuthors(self, authors):
        self.authors = authors
    def getAuthors(self):
        return self.authors
    def setJournal(self, journal):
        self.journal = journal
    def getJournal(self):
        return self.journal
    def setDate(self, date):
        self.date = date
    def getDate(self):
        return self.date
    def setYear(self, year):
        self.year = year
    def getYear(self):
        return self.year
    def setIssue(self, issue):
        self.issue = issue
    def getIssue(self):
        return self.issue
    def setPages(self, pages):
        self.pages = pages
    def getPages(self):
        return self.pages
    def setAbstract(self, abstract):
        self.abstract = abstract
    def getAbstract(self):
        return self.abstract
    def setVolume(self, volume):
        self.volume = volume
    def getVolume(self):
        return self.volume
    def setPrimaryAuthor(self, pAuthor):
        self.primaryAuthor = pAuthor
    def getPrimaryAuthor(self):
        return self.primaryAuthor
    def setPublicationType(self, publicationType):
        self.publicationType = publicationType
    def getPublicationType(self):
        return self.publicationType
    def setElocator(self, elocator):
        self.elocator = elocator
    def getElocator(self):
        return self.elocator
    # add other accessors as needed

class PubMedAgent:
        # Is: an agent that interacts with PubMed to get reference data
        #	for DOI IDs
        # Does: takes DOI IDs, queries PubMed, and returns PubMedReference
        #	objects for them

        def __init__ (self):
            # Purpose: constructor
            return

        def getPubMedID (self, doiID):
                # Purpose: return the PubMed ID corresponding to this doiID, or None
                #     if there is no corresponding PubMed ID
                # Throws: Exception if the URL returns an error
                # Notes: 6/30 - not tested

                return self.getPubMedIDs([doiID])[doiID]

        def getPubMedIDs (self, doiList):
            # Purpose: return a dictionary mapping from each DOI ID to its
            #     corresponding PubMed ID.  If no PubMed ID for a given DOI ID,
            #     then that one maps to None.
            # Throws: Exception if the URL returns an error
            mapping = {}  # {doiid: [pubMedId(s)], ...}
            try:
                #print '### Getting PubMed IDs ###\n'
                for doiID in doiList:
                    forUrl = doiID
                    forUrl = doiID.replace('(', '*')
                    forUrl = doiID.replace(')', '*')
                    forUrl = doiID.replace(';', '*')
                    forUrl = doiID.replace(':', '*')
                    idUrl = PUBMEDID_CONVERTER_URL % (XML, forUrl)
                    record = gov.get(idUrl.replace('[', '%5B').replace(']', '%5D'))
                    xmldoc = xml.dom.minidom.parseString(record)
                    pubmedIDs = xmldoc.getElementsByTagName("Id")
                    if doiID not in mapping:
                        mapping[doiID] = []
                    if pubmedIDs == []:
                        mapping[doiID].append(None)
                    else:
                        for pmID in pubmedIDs:
                            mapping[doiID].append(pmID.firstChild.data)
            except IOError as e:
                if hasattr(e, 'code'): # HTTPError
                    print('HTTP error code: ', e.code)
                    raise Exception('HTTP error code: %s' % e.code)
                elif hasattr(e, 'reason'): # URLError
                    print("Can't connect, reason: ", e.reason)
                    raise Exception("Can't connect, reason: %s" % e.reason)
                else:
                        raise Exception('Unknown exception: %s' % e)

            return mapping

        def getReferenceInfo(self, doiList):
                # Purpose: stub to be implemented by child
                return
        
        def getReference (self, doiID):
            # Purpose: returns a dictionary that maps each DOI ID to its
            #   corresponding PubMedReference object(s) (or None, if there
            #   is no reference data in PubMed for that DOI ID)
            # DOI ID can map to multiple PubMed 
            # sc - this has not been tested
                return self.getReferences([doiID])[doiID]

        def getReferences (self, doiList):
            # Purpose: returns a dictionary that maps each DOI ID to its
            #	corresponding PubMedReference object(s) (or None, if there
            #	is no reference data in PubMed for that DOI ID)
            # Notes: DOI ID can map to multiple PubMed

            # translate doiList to doiID/pubmedID dictionary
            # pubMedDict = {doiID:pubMedID, ...}
            #print 'getReferences doiList: %s' % doiList

            pubMedDict = self.getPubMedIDs(doiList)

            # call getReferenceInfo - which is implemented by the subclass.

            mapping = {}
            #print '### Getting PubMed References ###'
            for doiID in pubMedDict:
                if doiID not in mapping:
                    mapping[doiID] = []
                pubMedIdList = pubMedDict[doiID]
                refObject = None # default, for no pmID
                #print 'pubMedIdList: %s' % pubMedIdList
                for pubMedID in pubMedIdList:
                    if pubMedID == None:
                         mapping[doiID].append(refObject)
                    else:
                         refObject = self.getReferenceInfo(pubMedID)
                         mapping[doiID].append(refObject)
            return mapping
    
class PubMedAgentJson (PubMedAgent):
    # Is: an agent that interacts with PubMed to get reference data
    #	for DOI IDs
    # Does: takes DOI IDs, queries PubMed, and returns a JSON string
    #	for each reference
    # Note: Not implemented
    def __init__ (self):
        # Purpose: constructor
        return

    # override method used to format each reference, reporting JSON
    # for this class

class PubMedAgentMedline (PubMedAgent):
    # Is: an agent that interacts with PubMed to get reference data
    #	for DOI IDs
    # Does: takes DOI IDs, queries PubMed, and returns a Medline-formatted
    #	str.for each reference

    def __init__ (self):
        return

    # override method used to format each reference, reporting Medline
    # format for the PubMed request

    def getReferenceInfo(self, pubMedID):
        # Purpose: Implementation of the superclass stub. Given a pubMedID, get a
        #   MedLine record, parse, create and return a PubMedReference object
        # Throws: Exception if the URL returns an error
        # Init the reference we will return
        pubMedRef = None
        try:
            medLineRecord = gov.get(REFERENCE_FETCH_URL % (pubMedID, TEXT, MEDLINE))
        except IOError as e:
            if hasattr(e, 'code'): # HTTPError
                print('http error code: ', e.code)
                raise Exception('HTTP error code: %s' % e.code)
            elif hasattr(e, 'reason'): # URLError
                print("Can't connect, reason: ", e.reason)
                raise Exception("Can't connect, reason: %s" % e.reason)
            else:
                raise Exception('Unknown exception: %s' % e)

        # if this pubMedID returns an error, create reference object with
        # that error message, otherwise parse the record
        if medLineRecord.find('Error occurred:') !=  -1:
            pubMedRef = PubMedReference(errorMessage = medLineRecord)
        else: 
            pubMedRef = PubMedReference()
            tokens = str.split(medLineRecord, '\n')

            # Abstract, multilined w/o additional tag
            isAB = 0
            abList = []

            # author, multilined each with tag
            auList = []

            # title, multilined w/o additional tag
            isTI = 0
            tiList = []

            # publication type
            isPT = 0

            for line in tokens:
                # parse MedLine format

                #print line

                if isTI == 1:
                    if line.startswith('      '):
                        tiList.append(str.strip(line))
                        continue
                    else:
                        isTI = 0

                if isAB == 1:
                    if line.startswith('      '):
                        abList.append(str.strip(line))
                        #print(line)
                        continue
                    else:
                        isAB = 0

                # strip by first '-'
                try:
                    value = (list(map(str.strip,str.split(line, '-', 1))))[1]
                # else use entire line
                except:
                    value = str.strip(line)

                # tags of interest
                if line.startswith('PMID'):
                    pubMedRef.setPubMedID(value) 

                elif line.startswith('TI'):
                    isTI = 1
                    tiList.append(value)

                # skip 'AUID-'
                elif line.startswith('AU  -'):
                    if auList == []:
                        pubMedRef.setPrimaryAuthor(value)
                    auList.append(value)

                elif line.startswith('TA'):
                    pubMedRef.setJournal(value)

                elif line.startswith('DP'):
                    pubMedRef.setDate(value)
                    #print 'setting date in reference from: %s' % value
                    pubMedRef.setYear(str.split(value, ' ', 1)[0])

                elif line.startswith('IP'):
                    pubMedRef.setIssue(value)

                elif line.startswith('PG'):
                    pubMedRef.setPages(value)

                elif line.startswith('AB'):
                    isAB = 1
                    abList.append(value)

                elif line.startswith('VI'):
                    pubMedRef.setVolume(value)

                elif line.startswith('AID') and (line.find('[doi]') > 0):
                    pubMedRef.setDoiID(str.strip(line.split('AID -')[1].split('[')[0]))

                # find page numbers being stored in LID/[pii] (publisher item identifier)
                # this is known as the 'elocator' : XXXX can be anything;alphanumeric; case insensitive
                #       eXXX
                #       bioXXX
                #       devXXX
                #       dmmXXX
                #       jcsXXX
                #
                #       if E[0-9]xxx, then remove the E
                #
                elif line.startswith('LID') and (value.find('[pii]') > 0) and  \
                        (
                                value.lower().startswith('e')
                                or value.lower().startswith('bio')
                                or value.lower().startswith('dev')
                                or value.lower().startswith('dmm')
                                or value.lower().startswith('jcs')
                        ):

                    value = str.strip(line.split('LID -')[1].split('[')[0])

                    match = ELOCATOR_RE.search(value)
                    if match:
                        value = value.replace('E', '')

                    pubMedRef.setElocator(value)

                    # for testing
                    #pubMedRef.setElocator(line)

                elif line.startswith('PT'):

                    # find last PT or use list
                    if isPT == 0:
                        if value == 'Review':
                            pubMedRef.setPublicationType(value)
                            isPT = 1
                        elif value == 'Editorial':
                            pubMedRef.setPublicationType(value)
                            isPT = 1
                        elif value == 'Comment':
                            pubMedRef.setPublicationType(value)
                            isPT = 1
                        else:
                            pubMedRef.setPublicationType(value)

            #
            # remove non-ascii characters
            #
            abstract = ' '.join(abList)
            newAbstract = ''
            for c in abstract:
                if ord(c) < 128:
                    newAbstract += c
            pubMedRef.setAbstract(newAbstract)

            #pubMedRef.setAbstract(' '.join(abList))
            pubMedRef.setAuthors('; '.join(auList))
            pubMedRef.setTitle(' '.join(tiList))

        return pubMedRef
