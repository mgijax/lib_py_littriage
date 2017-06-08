# Name: PubMedAgent.py
# Purpose: to provide an easy means to fetch reference data from PubMed in
#	a variety of formats
# Usage:
# 1. call setToolName() and/or setEmailAddress() as desired to override
#	default values
# 2. instantiate a PubMedAgent, PubMedAgentJson, or PubMedAgentMedline
#	(depending on your desired return type)
# 3. start passing DOI IDs (singly or in a list) to the agent and getting
#	back data in your desired format

###--- Globals ---###

# name of tool making the request (sent to PubMed for tracking)
TOOL_NAME = 'PubMedAgent'

# email address in case contact is needed (sent to PubMed for tracking)
EMAIL_ADDRESS = 'mgi-help@jax.org'

# return Medline or Json format from PubMed request? (internal use)
MEDLINE = 'medline'
JSON = 'json'

# URL for sending DOI IDs to PubMed to be converted to PubMed IDs;
# need to fill in tool name, email address, and comma-delimited list of DOI IDs
ID_CONVERTER_URL = '''https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=%s&email=%s&ids=%s'''

# URL for sending PubMed IDs to PubMed to get reference data for them;
# need to fill in comma-delimited list of PubMed IDs, requested return mode,
# tool name, and email address
REFERENCE_FETCH_URL = '''https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=%s&retmode=%s&tool=%s&email=%s'''

###--- Functions ---###

def setToolName(tool):
	# change the tool name submitted to NCBI (for their tracking purposes)
	global TOOL_NAME

	TOOL_NAME = tool
	return

def setEmailAddress(email):
	# change email address submitted to NCBI (for their tracking purposes)
	global EMAIL_ADDRESS

	EMAIL_ADDRESS = email
	return

###--- Classes ---###

class PubMedReference:
	# Is: a Python representation of data for a single reference from 
	#	PubMed
	# Does: provides easy access within Python to reference attributes
	# Notes: if an errorMessage is provided rather than a jsonString, this
	#	PubMedReference will be flagged as isValid() == False, and the
	#	error message is then accessible from getErrorMessage().

	def __init__ (self, jsonString = None, errorMessage = None):
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

		if jsonString:
			# initialize this object from JSON data
			pass
		return

	###--- accessor methods ---###

	def isValid(self):
		return self.errorMessage == None

	def getErrorMessage(self):
		return self.errorMessage

	def getPubMedID(self):
		return self.pubMedID

	def getTitle(self):
		return self.title

	def getAuthors(self):
		return self.authors

	def getJournal(self):
		return self.journal

	def getDate(self):
		return self.date

	def getYear(self):
		return self.year

	def getIssue(self):
		return self.issue

	def getPages(self):
		return self.pages

	def getAbstract(self):
		return self.abstract

	# add other accessors as needed

class PubMedAgent:
	# Is: an agent that interacts with PubMed to get reference data
	#	for DOI IDs
	# Does: takes DOI IDs, queries PubMed, and returns PubMedReference
	#	objects for them

	def __init__ (self):
		return

	def getPubMedID (self, doiID):
		# return the PubMed ID corresponding to this doiID, or None
		# if there is no corresponding PubMed ID

		return self.getPubMedIDs([doiID])[doiID]

	def getPubMedIDs (self, doiList):
		# return a dictionary mapping from each DOI ID to its
		# corresponding PubMed ID.  If no PubMed ID for a given DOI ID,
		# then that one maps to None.

		# add in code here (function call?) to query PubMed, then
		# flesh out loop below

		mapping = {}
		for doiID in doiList:
			mapping[doiID] = None
		return mapping
	
	def getReference (self, doiID):
		# returns a single PubMedReference object for the DOI ID
		return self.getReferences([doiID])[doiID]

	def getReferences (self, doiList):
		# returns a dictionary that maps each DOI ID to its
		#	corresponding PubMedReference object (or None, if there
		#	is no reference data in PubMed for that DOI ID)

		# add in code here (function call?) to query PubMed, then
		# flesh out loop below

		# note that PubMed call should pull its requested format
		# from a method that can be overridden in subclasses (or from
		# an instance variable) -- JSON vs MEDLINE

		mapping = {}
		for doiID in doiList:
			# use function call to format the data for a given
			# reference appropriately (object, JSON, Medline), then
			# we can just override that function is subclasses
			# below.

			mapping[doiID] = None
		return mapping

class PubMedAgentJson (PubMedAgent):
	# Is: an agent that interacts with PubMed to get reference data
	#	for DOI IDs
	# Does: takes DOI IDs, queries PubMed, and returns a JSON string
	#	for each reference

	def __init__ (self):
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
	# format for this class

	# also need to adjust the requested format (JSON vs. MEDLINE) for
	# the PubMed request

