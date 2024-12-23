# Purpose: provides functions for extracting text from PDF files
#          and for finding DOI IDs in extracted text
# Notes: 
#	1. relies on MGI's litparser product to do the actual pdf to text
#	2. must be initialized with call to setLitParserDir()

import os
import re
import subprocess

###--- Globals ---###

LITPARSER = None        # full path to parsing script in litparser product

###--- Functions ---###

def setLitParserDir (
        directory	# string; path to the litparser product
        ):
        # Purpose: initialize this module by identifying where to find the
        #	litparser product.
        # Throws: Exception if 'directory' does not exist or if it does not
        #	contain the expected pdfGetFullText.sh script.

        global LITPARSER

        if not os.path.isdir(directory):
                raise Exception('%s is not a directory' % directory)

        LITPARSER = os.path.join(directory, 'pdfGetFullText.sh')
        if not os.path.exists(LITPARSER):
                raise Exception('%s does not exist' % LITPARSER)
        return
        
###--- Classes ---###

class DoiFinder (object):
    # Is: a parser that knows how find the DOI ID in the extracted text of a PDF
    # Has:  journal specific reg ex's and logic
    # Does: return the DOI ID in a text string

    # Define regex's as class variables so they are only compiled once,
    # and try to keep their definition near the code that uses them.

    # regex for detecting basic DOI IDs:
    # "10", followed by '.', followed by any number of 0-9 or '.' 
    # ... followed by anything else until we reach a space, tab, or semicolon
    DOI_RE = re.compile('(10\.[0-9\.]+/[^ \t;]+)')

    # regex specifically for recognizing IDs from any 10.1177 journal that
    #  contains trailing 'Journal'
    # 10.1177 is Sage publisher: https://us.sagepub.com/en-us/nam/sage-journals
    SAGE_DOI_RE = re.compile('(10\.1177/[a-zA-Z0-9\-\.]+)Journal')

    def getDoiID (self, text):
        # Purpose: return the DOI ID from the text, where text is the
        #          extracted text from a PDF.
        # Returns: string DOI ID or None (if no ID can be found)

        if text.find('www.pnas.org') >= 0:
            return self._getPnasID(text)

        # Everything except pnas
        text = text.replace(' journal.pone', 'journal.pone')
        text = text.replace(' j.isci', 'j.isci')
        match = self.DOI_RE.search(text)

        if not match:           # no apparent DOI
            return None

        # Got an ID match, lets see if it needs any special handling
        doiID = match.group(1)
        slash = doiID.find('/')         # where is the 1st '/'
        nl = doiID.find('\n')           # where is the 1st '\n'

        # special case for PLoS journals, which often have a line break in ID.
        # PLOS journals have 28-character DOI IDs 99.98% of the time.
        # Out of 10,000+ # PLOS DOI IDs in MGI so far, the only others are
        #   single IDs with 21 and 24 characters. 
        # So if we encounter a newline within the first 21 characters,
        #   we can just remove it.
        # Also as of new pdftotext util we started using in Oct 2019, the 1st
        #  or 2nd ID occurrance in the paper may be truncated when a space is
        #  inserted instead of a line break.
        #  So try looking for a couple ID instances.
        if doiID.startswith('10.1371/'):        # PLoS
            if (0 <= nl < 21):	# remove potential nl
                doiID = doiID.replace('\n', '', 1)
                slash = doiID.find('/')
                nl = doiID.find('\n')
            i = 0
            while len(doiID) < 28:		# try another occurrance
                if i == 3: break	# quit after 3 tries
                i += 1

                match = self.DOI_RE.search(text, match.end())
                if not match: break	# odd, this shouldn't happen, bail
                doiID = match.group(1)
                slash = doiID.find('/')
                nl = doiID.find('\n')

                if (0 <= nl < 21):	# remove potential nl
                    doiID = doiID.replace('\n', '', 1)
                    slash = doiID.find('/')
                    nl = doiID.find('\n')

        # Special case for Journals from American Society for Microbiology (ASM)
        # Includes Molecular and Cellular Biology (also J Virol, MBio (mBio?),
        #  Infec Immun)
        # These have DOI IDs from 20 to 32 characters
        #   -- but which are often interrupted by line breaks
        # in their new (circa late-2016) PDF format. As workaround for the most
        # common case, remove any newlines within the first 20 chars of the ID.
        if doiID.startswith('10.1128/'):
            while 0 <= nl < 20:
                doiID = doiID.replace('\n', '', 1)
                nl = doiID.find('\n')
        
        # This code is not journal specific. It would be nice to refactor
        #   and have all the non-journal specific code in one place, but
        #   this is a little scary to move.

        # if there is a newline right after the slash, just remove it
        if (nl >= 0) and (nl == (slash+1)):
            doiID = doiID.replace('\n', '', 1)
            nl = doiID.find('\n')

        # if there is a newline later in the string,
        # trim the ID at that point
        if (nl >= 0) and (nl > slash):
            doiID = doiID[:nl]

        doiID = self._cleanEnd(doiID)   # rm trailing ')', ']', '.', whitespace

        # Now back to journal specific code...

        # if this is a '10.1177/...Journal' DOI ID,  (Sage journals)
        # then remove the trailing 'Journal' text
        if self.SAGE_DOI_RE.match(doiID):
            doiID = doiID.replace('Journal', '')

        elif (doiID.find('/eLife') > 0) and (doiID.endswith('.001')):
            doiID = doiID[:-4]       # eLife IDs often errantly end with .001

        elif doiID.startswith('10.1182/blood'):
            doiID = self._getBloodID(text)

        elif doiID.startswith('10.1172/jci'):
            doiID = self._getJciInsightID(text)

        elif doiID.startswith('10.1530/REP'):
            doiID = self._getReproductionID(text)

        # if this is a Science DOI ID, we instead need to find and return the
        #   last DOI ID for the PDF file.
        # scitranslmed is from the same publisher (like scisignal) but is not
        #   handled here.
        # I haven't found any examples in our db from scitranslmed or scisignal
        #   where the 1st doi is the wrong one (haven't looked too hard either)
        elif doiID.startswith('10.1126/science') or \
            doiID.startswith('10.1126/scisignal'):
            doiID =  self._getScienceID(text)

        return doiID
    # end getDoiID() --------------

    END_CLEAN_RE = re.compile('[\)\.\]\s]+$')
    def _cleanEnd (self, text):
        # strip off trailing parentheses, periods, 
        # brackets, and whitespace from the text
        text = self.END_CLEAN_RE.sub('', text)
        return text

    # regex specifically for recognizing IDs from Blood journal
    BLOOD_DOI_RE = re.compile('10\.1182/blood([0-9\-\.\s]+)')
    # (6/25/2020) Note Blood has at least two types of articles, full articles
    #  e.g., MGI:6284584 and "comment" (or short?) artcles like MGI:6284578.
    # In the comment articles, the PDF for an article often contains the tail
    #   end of a previous article in the issue, and may contain the beginning
    #   of the the next article, full articles. These tail/beginning parts of
    #   the surrounding articles may contain their own DOI IDs.
    #   So it is easy to get the wrong (but valid!) DOI ID.
    # In our download files, often there is a download page at the end that
    #  contains the correct DOI ID. Probably should change the logic to get
    #  that ID from the PDF (should consider what happens w/ supp data, haven't
    #  looked for examples of that)
    # Blood also has two types of IDs:
    #   hyphenated:   '10.1182/blood-2018-12-889758'
    #   unhyphenated: '10.1182/blood.2019004603'  (seems to always start w/ '.')
    #   The code below 
    # Given all the pain here, best solution is to have Quosa name the
    #  downloaded PDFs using the PMID_##### convention so we don't have to
    #  try to find the DOI ID in the text.  See TR12755.

    def _getBloodID (self, text):
        # if this is a Blood DOI ID, 
        # the hypenation sometimes needs tweaking
        # may contain a '.' or a ' '
        # Note: Blood really needs better logic, often
        #  the 1st doiID is for the paper in the PDF.
        #  Should probably grab last doiID like Science.
        match   = self.BLOOD_DOI_RE.search(text)
        doiID   = self._cleanEnd(match.group(0))
        numbers = self._cleanEnd(match.group(1))
        revised = self._BloodFixHyphens(numbers)
        doiID = doiID.replace(numbers, revised)
        doiID = doiID.replace(' ', '')
        doiID = doiID.replace('\n', '')

        return doiID
    # end _getBloodID() --------------

    def _BloodFixHyphens (self, s):
        # Purpose: fix the hyphenation in Blood DOI IDs, which should be
        #	of the format "-yyyy-mm-others" where the first six digits
        #	are the year, the next two are the month, and then all the
        #	others come at the end
        # Returns: string updated according to 'Purpose', or the input string
        #	if there are not enough digits
        digits = s.replace('-', '').replace('.', '').replace(' ', '')
        if len(digits) < 7:
            return s
        if s.find('.') >= 0:
            return '.%s%s%s' % (digits[:4], digits[4:6], digits[6:])
        else:
            return '-%s-%s-%s' % (digits[:4], digits[4:6], digits[6:])
    # end _BloodFixHyphens() --------------

    # Reproduction: regex specifically for recognizing IDs from any 10.1530/REP
    REP_DOI_RE = re.compile('(?:doi.org/)?(10\.1530/REP[ \-0-9]+)')
    def _getReproductionID (self, text):
        # Reproduction may have spaces introduced
        #   and newer papers have 'doi.org/'
        match = self.REP_DOI_RE.search(text)
        doiID = match.group(1)
        doiID = doiID.replace(' ', '')
        return doiID
    # end _getReproductionID() --------------

    # regex specifically for recognizing IDs from any 10.1172/jci. insight
    #  may have line break (which may get translated to ' ' by pdftotext) after
    #  'jci.'
    JCI_DOI_RE = re.compile('(10\.1172/jci\.[\s]?insight\.[0-9]+)')
    def _getJciInsightID (self, text):
        match = self.JCI_DOI_RE.search(text)
        doiID = match.group(0)
        doiID = doiID.replace(' ', '')
        doiID = doiID.replace('\n', '')
        return doiID
    # end _getJciInsightID() --------------

    # regex for recognizing IDs from Proc Natl Acad Sci (PNAS) journal
    # examples: matches 
    # 10.1073/pnas.0931458100 OR 10.1073pnas.0931458100 OR 
    # 10.1073#pnas.0931458100 f
    #\W? match 0 or 1 non-alphanumeric between '10.1073' and 'pnas'
    PNAS_DOI_RE = re.compile('(10\.1073\W?pnas\.[0-9]+)')
    def _getPnasID (self, text):
        # PNAS DOI sometimes have missing '/' e.g., '10.1073pnas.041475098'
        #   so can't be found using our standard DOI_RE
        # Determine if missing '/' OR intervening SINGLE non-alphnumeric char
        #   should be replaced by '/'
        match = self.PNAS_DOI_RE.search(text)
        doiID = match.group(1)

        if doiID.find('/') == -1:       # no '/'
            if doiID.find('pnas') == 7: # there is no '/', add one
                doiID = doiID.replace('10.1073', '10.1073/')
            elif doiID.find('pnas') == 8: # there is a single intervening char
                # jak: this is really rare
                charToReplace = doiID[7]
                doiID = doiID.replace(charToReplace, '/')
        return doiID
    # end _getPnasID() --------------

    # regex specifically for recognizing IDs from Science journals
    SCIENCE_DOI_RE = re.compile('(10\.1126/[a-zA-Z0-9\-\.]+)')
    # regex for finding "accepted" string
    ACCEPTED_RE = re.compile('accepted', re.IGNORECASE)
    def _getScienceID (self, text):
        # Science journals include the end of the prior article at the
        # start of the PDF file.  This means that we will usually
        # return an inaccurate DOI ID for PDFs from Science journals.
        # Instead, the desired ID occurs at the end of the article,
        # shortly after the word "accepted".  Use these criteria to
        # get the desired ID and return it.

        # To get to this method, we must have already loaded the
        # full text, and it must have been non-null.

        # Find all occurrences of the word 'accepted' and note the
        # position of each.  (It is possible that 'accepted' would
        # occur in the start of the next article, so we can't just
        # blindly take the last one.)

        acceptedPositions = []
        match = self.ACCEPTED_RE.search(text)
        while match:
            pos = match.regs[0][0]
            acceptedPositions.append(pos)
            match = self.ACCEPTED_RE.search(text, pos + 1)

        # Now start at the last occurrence of "accepted" and see if
        # we can find a Science DOI ID reasonably soon after it.  If
        # so, that's our desired ID to return.  If not, work back
        # through the other instances of "accepted".

        # how close is close enough? (number of characters)
        threshold = 80
        acceptedPositions.reverse()

        for accPos in acceptedPositions:
            match = self.SCIENCE_DOI_RE.search(text, accPos)
            if match:
                if (match.regs[0][0] <= (accPos + threshold)):
                    return match.group(1)
        return None 
    # end _getScienceID() --------------
# end class DoiFinder -------------------

class PdfParser:
        # Is: a parser that knows how to extract text from a PDF file
        # Has: path to a PDF file, text from a PDF file
        # Does: reads a PDF file from the file system, parses it, provides
        #	access to full text and various bits of information

        doiFinder = DoiFinder()         # only need a singleton DoiFinder

        def __init__ (self,
                pdfPath		# string; path to PDF file to parse
                ):
                # Purpose: constructor
                # Throws: Exception if the file specified in 'pdfPath' does
                #	not exist

                if not os.path.exists(pdfPath):
                        raise Exception('PDF file does not exist: %s' % pdfPath)

                self.pdfPath = pdfPath	# string; path to the PDF file
                self.fullText = None	# string; text from the PDF file
                self.loaded = False	# boolean; did we read the file yet?
                return

        def _loadFullText (self):
                # Purpose: (private) get the text from the PDF file
                # Throws: Exception if this library has not been properly
                #	initialized or if there are errors in parsing the file
                # Notes: only loads the file once; if we already ready it,
                #	calling this function is a no-op.

                if self.loaded:
                        return

                if not LITPARSER:
                        raise Exception('Must initialize pdfParser library using setLitParserDir()')

                self.stderr = ''
                cmd = [ LITPARSER, self.pdfPath ]
                cmdText = ' '.join(cmd)
                try:
                        completedProcess = subprocess.run(cmd, text=True,
                                                            capture_output=True)
                except: # error in attempting to execute parsing script
                        raise Exception('Failed to execute: %s' % cmdText)

                self.stderr = completedProcess.stderr

                # parsing script finished with an error code?
                if (completedProcess.returncode != 0):
                        msg = 'Failed to parse %s\n' % self.pdfPath
                        msg += 'Stderr from %s:\n%s\n' % (cmdText, self.stderr)
                        raise Exception(msg)

                # parsing was successful, so grab the text and note that we
                # loaded the file
                self.fullText = completedProcess.stdout
                self.loaded = True
                return

        def getStderr(self):
                return self.stderr

        def getFirstDoiID (self):
                # Purpose: return the first DOI ID from the PDF file
                # Returns: string DOI ID or None (if no ID can be found)
                # Throws: Exception if this library has not been properly
                #	initialized or if there are errors in parsing the file
                # Note: this would be more aptly named getDoiID()

                self._loadFullText()

                if self.fullText:
                        return self.doiFinder.getDoiID(self.fullText)
                else:
                        return None

        def getText (self):
                # Purpose: return the full text extracted from the PDF file
                # Returns: string (full text)

                self._loadFullText()
                if self.fullText:
                        return self.fullText
                return None
# end class PdfParser  -------------------
