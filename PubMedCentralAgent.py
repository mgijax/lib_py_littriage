# Name: PubMedCentralAgent.py
# Purpose: provide an interface to various services at PubMed Central
# Usage: 
#	1. Initialize the module by calling setToolName() and/or setEmailAddress() as desired to override
#	default settings.
#	2. Instantiate an IDCoverterAgent (to convert DOI IDs to PMC IDs) or a PDFLookupAgent (to take
#	PMC IDs and look up)
#	3. Run with it.

import urllib2
import xml.dom.minidom 
import HttpRequestGovernor

###--- Globals ---###

# name of tool making the request (sent to PubMed for tracking)
TOOL_NAME = 'PubMedCentralAgent'

# email address in case contact is needed (sent to PubMed for tracking)
EMAIL_ADDRESS = 'mgi-help@jax.org'

# URL for sending DOI IDs to PubMed Central to be converted to PubMed Central (PMC) IDs;
# need to fill in tool name, email address, and comma-delimited list of DOI IDs
ID_CONVERTER_URL = '''https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=%s&email=%s&ids=%s&format=csv'''

# URL for sending a PubMed Central (PMC) ID to PubMed Central to get its download URLs
# need to fill in a single PMC ID
PDF_LOOKUP_URL = '''https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=%s'''

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

def _splitList (
    items,   # the list of items to split
    n        # the maximum number of items per sublist
    ):
    # Purpose: (private) splits 'items' in a list of sub-lists, each of which has 'n' or fewer items in it
    # Returns: list of lists as described in Purpose
    # Example:
    #    _splitList ( [ 'a', 'b', 'c', 'd', 'e' ], 2) ===> [ ['a', 'b'], ['c', 'd'], ['e'] ]

    if len (items) <= n:
        return [ items ]
    else:
        return [ items [:n] ] + _splitList (items [n:], n)

###--- Classes ---###

class IDConverterAgent:
    # Is: an agent that communicates with PubMed Central to convert DOI IDs to PMC IDs
    
    def __init__ (self):
        return
    
    def getPMCID (self, doiID):
        # Purpose: look up the PMC ID for a single DOI ID
        # Returns: string (PMC ID) or None (if the DOI ID has no PMC ID)
        # Throws: Exception if there are problems communicating with PubMed Central
        
        return self.getPMCIDs([ doiID ])[doiID]
    
    def getPMCIDs (self, doiIDs):
        # Purpose: look up the PMC ID corresponding to each DOI ID in the input list
        # Returns: dictionary mapping from each DOI ID to its corresponding PMC ID (or None,
        #    if a given DOI ID has no PMC ID)
        # Throws: Exception if there are problems communicating with PubMed Central
        
        pmcIDs = {}     # maps from DOI ID to PMC ID
        if not doiIDs:
            return pmcIDs

        # strip leading & trailing spaces from IDs and split the list into chunks
        sublists = _splitList(map(lambda x : x.strip(), doiIDs), 20)

        for sublist in sublists:
            lines = HttpRequestGovernor.readURL(ID_CONVERTER_URL % (TOOL_NAME, EMAIL_ADDRESS, ','.join(sublist)))
            
            # Lines have comma-delimited columns.  String values are in double-quotes.
            # Standardize lines by stripping out the double-quotes, then splitting on commas.
            lines = map(lambda x: x.split(','), lines.replace('"', '').split('\n'))
            
            # first line will have column headers.  We need DOI and PMCID columns.
            if 'DOI' not in lines[0]:
                raise Exception('Cannot find "DOI" column in getPMCIDs')
            if 'PMCID' not in lines[0]:
                raise Exception('Cannot find "PMCID" column in getPMCIDs')
            
            doiCol = lines[0].index('DOI')
            pmcCol = lines[0].index('PMCID')
            
            # now go through the rest of the lines and do the mapping

            for line in lines[1:]:
                if len(line) > pmcCol:
                    if line[pmcCol] != '':
                        pmcIDs[line[doiCol]] = line[pmcCol]
                    else:
                        pmcIDs[line[doiCol]] = None
                
        return pmcIDs 
    
class PDFLookupAgent:
    def __init__ (self):
        return
    
    def getUrl (self, pmcID):
        # Purpose: look up the download URL for a single PMC ID
        # Returns: string (URL) or None (if the PMC ID has no file to download)
        # Throws: Exception if there are problems communicating with PubMed Central
        
        return self.getUrls([ pmcID ])[pmcID]
    
    def getUrls (self, pmcIDs):
        # Purpose: look up the download URL corresponding to each PMC ID in the input list
        # Returns: dictionary mapping from each PMC ID to its corresponding download URL (or None,
        #    if a given PMC ID has no download URL)
        # Throws: Exception if there are problems communicating with PubMed Central
        # Notes: Direct links to PDF files are preferred, but if a given ID doesn't have one, we
        #    will fall back on a link to a tarred, gzipped directory, where available.
        
        urls = {}       # maps from PMC ID to download URL
        if not pmcIDs:
            return urls

        for pmcID in map(lambda x: x.strip(), pmcIDs):
            lines = HttpRequestGovernor.readURL(PDF_LOOKUP_URL % pmcID)
            xmldoc = xml.dom.minidom.parseString(lines)

            links = {}      # maps from format to url for this pmcID
            
            for linkElement in xmldoc.getElementsByTagName("link"):
                format = linkElement.attributes['format'].value
                url = linkElement.attributes['href'].value
                links[format] = url
                
            if 'pdf' in links:                  # prefer direct PDF over tarred, gzipped directory
                urls[pmcID] = links['pdf']
            elif 'tgz' in links:
                urls[pmcID] = links['tgz']
            else:
                urls[pmcID] = None
        
        return urls