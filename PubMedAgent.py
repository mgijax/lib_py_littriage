# Name: PubMedAgent.py
# Purpose: to provide an easy means to fetch reference data from PubMed in
#	a variety of formats
# Usage:
# 1. call setToolName() and/or setEmailAddress() as desired to override
#	default values
# 2. instantiate a PubMedAgent, PubMedAgentJson, or PubMedAgentMedline
#	(depending on your desired return type)
# 3. start passing DOI IDs (singly or in a list) to the agent and getting
#	back data in your desired format using getReference(doiID) or getReferences(doiList)

import string
import urllib
import csv
import xml.dom.minidom 

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

# URL for sending DOI IDs to PubMed to be converted to PubMed IDs;
# need to fill in tool name, email address, and comma-delimited list of DOI IDs
#ID_CONVERTER_URL = '''https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=%s&email=%s&format=csv&ids=%s'''
ID_CONVERTER_URL = '''https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&retmode=%s&term=%s'''

# URL for sending PubMed IDs to PubMed to get reference data for them;
# need to fill in comma-delimited list of PubMed IDs, requested return mode,
# tool name, and email address
#REFERENCE_FETCH_URL = '''https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=%s&retmode=%s&tool=%s&email=%s'''
REFERENCE_FETCH_URL = '''https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=%s&retmode=%s&rettype=%s'''

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
	self.title = None
	self.authors = None
	self.journal = None
	self.date = None
	self.year = None
	self.issue = None
	self.pages = None
	self.abstract = None
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
		    #print ID_CONVERTER_URL % (XML, doiID)
		    response = urllib.urlopen(ID_CONVERTER_URL % (XML, forUrl))
		    record = string.strip(response.read())
		    #print record
		    xmldoc = xml.dom.minidom.parseString(record)
		    pubmedIDs = xmldoc.getElementsByTagName("Id")
		    if doiID not in mapping:
			mapping[doiID] = []
		    if pubmedIDs == []:
			mapping[doiID].append(None)
		    else:
			for pmID in pubmedIDs:
			    #print 'pm: %s' % pmID.firstChild.data
			    mapping[doiID].append(pmID.firstChild.data)
	    except IOError, e:
		if hasattr(e, 'code'): # HTTPError
		    print 'HTTP error code: ', e.code
		    raise Exception('HTTP error code: %s' % e.code)
		elif hasattr(e, 'reason'): # URLError
		    print "Can't connect, reason: ", e.reason
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
    #	string for each reference

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
	    #print REFERENCE_FETCH_URL % (pubMedID, TEXT, MEDLINE)
	    response = urllib.urlopen(REFERENCE_FETCH_URL % (pubMedID, TEXT, MEDLINE))
	    medLineRecord = string.strip(response.read())
	    print '"%s"' % medLineRecord
	except IOError, e:
	    if hasattr(e, 'code'): # HTTPError
		print 'http error code: ', e.code
		raise Exception('HTTP error code: %s' % e.code)
	    elif hasattr(e, 'reason'): # URLError
		print "Can't connect, reason: ", e.reason
		raise Exception("Can't connect, reason: %s" % e.reason)
	    else:
		raise Exception('Unknown exception: %s' % e)

	# if this pubMedID returns an error, create reference object with
	# that error message, otherwise parse the record
	if string.find(medLineRecord, 'Error occurred:') !=  -1:
	    pubMedRef = PubMedReference(errorMessage = medLineRecord)
	else: 

	    pubMedRef = PubMedReference()
	    tokens = string.split(medLineRecord, '\n')

	    # Abstract, multilined w/o additional tag
	    isAB = 0
	    abList = []

	    # author, multilined each with tag
	    auList = []

	    # title, multilined w/o additional tag
	    isTI = 0
	    tiList = []
	    for line in tokens:
		#print line
		# handle multilined Abstract
		if isAB == 1 and line.startswith('      '):
		    # strip the leading spaces
		    abList.append(string.strip(line))
		else:
		    isAB = 0
		    # check for other continues lines we don't care about
		    # e.g. AD
		    if not line.startswith('      '):
			value = (map(string.strip,string.split(line, '-')))[1]
		    else:
			continue
		# handle multilined Title
		if isTI == 1 and line.startswith('      '):
		    # strip the leading spaces
		    tiList.append(string.strip(line))
		else:
		    isTI = 0
		    # check for other continues lines we don't care about
		    # e.g. AD
		    if not line.startswith('      '):
			value = (map(string.strip,string.split(line, '-', 1)))[1]
		    else:
			continue
		# parse MedLine format
		if line.startswith('PMID'):
		    pubMedRef.setPubMedID(value) 
		elif line.startswith('TI'):
		    isTI = 1
		    tiList.append(value)
		elif line.startswith('AU'):
		    auList.append(value)
		elif line.startswith('TA'):
		    pubMedRef.setJournal(value)
		elif line.startswith('DP'):
		    pubMedRef.setDate(value)
		    print 'setting date in reference from: %s' % value
		    pubMedRef.setYear(string.split(value, ' ', 0))
		elif line.startswith('IP'):
		    pubMedRef.setIssue(value)
		elif line.startswith('PG'):
		    pubMedRef.setPages(value)
		elif line.startswith('AB'):
		    isAB = 1
		    abList.append(value)
	    pubMedRef.setAbstract(string.join(abList))
	    pubMedRef.setAuthors(string.join(auList, ', '))
	    pubMedRef.setTitle(string.join(tiList))
	return pubMedRef
