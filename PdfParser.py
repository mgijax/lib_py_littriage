# Name: pdfParser.py
# Purpose: provides functions for extracting text from PDF files
# Notes: 
#	1. relies on MGI's litparser product to do the actual processing
#	2. must be initialized with call to setLitParserDir()

import os
import re
import runCommand

###--- Globals ---###

# full path to parsing script in litparser product
LITPARSER = None

# regex for detecting DOI IDs, with:
# 1. DOI prefix (case insensitive)
# 2. may be followed by a colon or space (or not)
# 3. followed by anything else until we reach a space, tab, or semicolon
# 10,  followed by '.', followed by any number of 0-9 or '.' 
DOI_RE = re.compile('(10\.[0-9\.]+/[^ \t;]+)')

# regex specifically for recognizing IDs from Blood journal
BLOOD_DOI_RE = re.compile('10\.1182/blood([0-9\-\.\s]+)')
# (6/25/2020) Note Blood has at least two types of articles, full articles
#  e.g., MGI:6284584 and "comment" (or short?) artcles like MGI:6284578.
# In the comment articles, the PDF for an article often contains the tail
#   end of a previous article in the issue, and may contain the beginning
#   of the the next article, full articles. These tail/beginning parts of
#   the surrounding articles may contain their own DOI IDs.
#   So it is easy to get the wrong (but valid!) DOI ID.
# It appears that in our download files, there is a download page at the end
#  that contains the correct DOI ID. Probably should change the logic to get
#  that ID from the PDF  (should consider what happens with supp data, haven't
#  looked for examples of that)
# See TR12755.

# regex specifically for recognizing IDs from Science journals
SCIENCE_DOI_RE = re.compile('(10\.1126/[a-zA-Z0-9\-\.]+)')

# regex specifically for recognizing IDs from any 10.1177 journal that contains trailing 'Journal'
# 10.1177 is Sage publisher: https://us.sagepub.com/en-us/nam/sage-journals
JOURNAL_DOI_RE = re.compile('(10\.1177/[a-zA-Z0-9\-\.]+)Journal')

# regex specifically for recognizing IDs from any 10.1172/jci. insight
JCI_DOI_RE = re.compile('(10\.1172/jci\. insight\.[0-9]+)')

# regex specifically for recognizing IDs from any 10.1530/REP
REP_DOI_RE = re.compile('(doi.org/10\.1530/REP[ \-0-9]+)')

# regex for finding "accepted" string
ACCEPTED_RE = re.compile('accepted', re.IGNORECASE)

# regex specifically for recognizing IDs from Proc Natl Acad Sci (PNAS) journal
# examples: matches 
# www.pnas.org/cgi/doi/10.1073/pnas.0931458100 OR www.pnas.orgcgidoi10.1073pnas.0931458100 OR 
# www.pnas.orgcgidoi10.1073#pnas.0931458100 f
#\W? match 0 or 1 non-alphanumeric between '10.1073' and 'pnas'
PNAS_DOI_RE = re.compile('(10\.1073\W?[pnas\.[0-9]+)')
#          this '[' shouldn't be here ^

# this one matches optional '/' between '10.1073' and 'pnas'
#PNAS_DOI_RE = re.compile('(10\.1073/*pnas\.[0-9]+)')

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
	
def hyphenate (s):
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

###--- Classes ---###

class PdfParser:
	# Is: a parser that knows how to extract text from a PDF file
	# Has: path to a PDF file, text from a PDF file
	# Does: reads a PDF file from the file system, parses it, provides
	#	access to full text and various bits of information

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
		cmd = '%s %s' % (LITPARSER, self.pdfPath)
		try:
			(stdout, stderr, exitCode) = runCommand.runCommand(cmd)
		except:
			# error in attempting to execute parsing script
			raise Exception('Failed to execute: %s' % cmd)

		# parsing script finished with an error code?
		if (exitCode != 0):
                        self.stderr = stderr
			msg = 'Failed to parse %s\n' % self.pdfPath
                        msg += 'Stderr from %s:\n%s\n' % (cmd, stderr)
			raise Exception(msg)

		# parsing was successful, so grab the text and note that we
		# loaded the file

		self.fullText = stdout
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

			# PNAS only
			if self.fullText.find('www.pnas.org') >= 0:

			    	match = PNAS_DOI_RE.search(self.fullText)
				doiID = match.group(1)

				# may have DCSupplemental - TR 13224
				try:
					if self.fullText.find('DCSupplemental') >= 0:
						doiID = match.group(2)
                                                # there never is a group 2 in RE
                                                # should always raise exception
				except:
					pass

			    	# PNAS DOI sometimes have missing '/' so can't be found using DOI_RE
			    	# determine if missing '/' OR intervening SINGLE non-alphnumeric char
				# if no '/' 
				if doiID.find('/') == -1:
				  	if doiID.find('pnas') == 7: # there is no '/', add one
						doiID = doiID.replace('10.1073', '10.1073/')
				   	elif doiID.find('pnas') == 8: # there is a single intervening char
                                                # jak: this is really rare
						charToReplace = doiID[7]
						doiID = doiID.replace(charToReplace, '/')
				return doiID

			# all else
			else:
				self.fullText = self.fullText.replace(' journal.pone', 'journal.pone')
				match = DOI_RE.search(self.fullText)

			if match:
				doiID = match.group(1)
				slash = doiID.find('/')
				nl = doiID.find('\n')

				# special case for PLoS journals, which often have a line break in the ID.
				# PLOS journals have 28-character DOI IDs 99.98% of the time.  Out of 10,000+
				# PLOS DOI IDs in MGI so far, the only others are single IDs with 21 and 24
				# characters.  So if we encounter a newline within the first 21 characters,
				# we can just remove it.
				# Also as of new pdftotext util we started using in Oct 2019, the 1st or 2nd
				#  ID occurrance in the paper may be truncated when a space is inserted
				#  instead of a line break. So try looking for a couple ID instances.

				if doiID.startswith('10.1371/'):
					if (0 <= nl < 21):	# remove potential nl
						doiID = doiID.replace('\n', '', 1)
						slash = doiID.find('/')
						nl = doiID.find('\n')
					i = 0
					while len(doiID) < 28:		# try another occurrance
						if i == 3: break	# quit after 3 tries
						i += 1

						match = DOI_RE.search(self.fullText, match.end())
						if not match: break	# odd, this shouldn't happen, bail
						doiID = match.group(1)
						slash = doiID.find('/')
						nl = doiID.find('\n')

						if (0 <= nl < 21):	# remove potential nl
							doiID = doiID.replace('\n', '', 1)
							slash = doiID.find('/')
							nl = doiID.find('\n')

				# special case for Journals from American Society for Microbiology (ASM)
                                # includes Molecular and Cellular Biology
                                # (also J Virol, MBio (mBio?), Infec Immun)
                                # These have DOI IDs from 20 to 32 characters
                                #   -- but which are often interrupted by line breaks
				# in their new (circa late-2016) PDF format.  As a workaround for the most
				# common case, remove any newlines within the first 20 characters of the ID.
				
				if doiID.startswith('10.1128/'):
					while 0 <= nl < 20:
						doiID = doiID.replace('\n', '', 1)
						nl = doiID.find('\n')
				
				# if there is a newline right after the slash,
				# just remove it

				if (nl >= 0) and (nl == (slash+1)):
					doiID = doiID.replace('\n', '', 1)
					nl = doiID.find('\n')

				# if there is a newline later in the string,
				# trim the ID at that point

				if (nl >= 0) and (nl > slash):
					doiID = doiID[:nl]

				# strip off trailing parentheses, periods, 
				# brackets, and whitespace
				doiID = re.sub('[\)\.\]\s]+$', '', doiID)

				# eLife IDs often errantly end with .001
				if (doiID.find('/eLife') > 0) and (doiID.endswith('.001')):
					doiID = doiID[:-4]

				# if this is a Blood DOI ID, 
				# the hypenation sometimes needs tweaking
				# may contain a '.' or a ' '
                                # Note: Blood really needs better logic, often
                                #  the 1st doiID is for the paper in the PDF.
                                #  Should probably grab last doiID like Science.
				if doiID.startswith('10.1182/blood'):
					match = BLOOD_DOI_RE.search(self.fullText)
					doiID = match.group(0)
					numbers = match.group(1)
					revised = hyphenate(numbers)
					doiID = doiID.replace(numbers, revised)
					doiID = doiID.replace(' ', '')
					doiID = doiID.replace('\n', '')

				if doiID.startswith('10.1172/jci'):
					match = JCI_DOI_RE.search(self.fullText)
					doiID = match.group(0)
					doiID = doiID.replace(' ', '')

				if doiID.startswith('10.1530/REP'):
					match = REP_DOI_RE.search(self.fullText)
                                        # 6/26/2020: this errors on older papers
                                        #   now that don't have 'doi.org/'
					doiID = match.group(0)
					doiID = doiID.replace('doi.org/', '')
					doiID = doiID.replace(' ', '')

				# if this is a 10.1177/...Journal DOI ID, 
				# then remove the trailing 'Journal' text
				match = JOURNAL_DOI_RE.match(doiID)
				if match:
					doiID = doiID.replace('Journal', '')

				# if this is a Science DOI ID, we instead need
				# to find and return the last DOI ID for the
				# PDF file.
                                # scitranslmed is from the same publisher (like
                                #   scisignal) but is not handled here.
                                # I haven't found any examples in
                                #   our db from scitranslmed or scisignal where
                                #   the 1st doi is the wrong one (haven't looked
                                #   too hard either)
				if doiID.startswith('10.1126/science') or \
					doiID.startswith('10.1126/scisignal'):
				        doiID =  self._getScienceID()

				return doiID
		return None

	def _getScienceID (self):
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
		match = ACCEPTED_RE.search(self.fullText)
		while match:
			pos = match.regs[0][0]
			acceptedPositions.append(pos)
			match = ACCEPTED_RE.search(self.fullText, pos + 1)

		# Now start at the last occurrence of "accepted" and see if
		# we can find a Science DOI ID reasonably soon after it.  If
		# so, that's our desired ID to return.  If not, work back
		# through the other instances of "accepted".

		# how close is close enough? (number of characters)
		threshold = 80
		acceptedPositions.reverse()

		for accPos in acceptedPositions:
			match = SCIENCE_DOI_RE.search(self.fullText, accPos)
			if match:
				if (match.regs[0][0] <= (accPos + threshold)):
					return match.group(1)
		return None 

	def getText (self):
		# Purpose: return the full text extracted from the PDF file
		# Returns: string (full text)

		self._loadFullText()
		if self.fullText:
			return self.fullText
		return None
