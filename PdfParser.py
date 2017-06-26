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
DOI_RE = re.compile('(10\.[0-9\.]+/[^ \t;]+)')
BLOOD_DOI_RE = re.compile('10\.1182/blood([0-9\-]+)')

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

	digits = s.replace('-', '')
	if len(digits) < 7:
		return s
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

		cmd = '%s %s' % (LITPARSER, self.pdfPath)
		try:
			(stdout, stderr, exitCode) = runCommand.runCommand(cmd)
		except:
			# error in attempting to execute parsing script
			raise Exception('Failed to execute: %s' % cmd)

		# parsing script finished with an error code?
		if (exitCode != 0):
			raise Exception('Failed to parse %s' % self.pdfPath)

		# parsing was successful, so grab the text and note that we
		# loaded the file

		self.fullText = stdout
		self.loaded = True
		return

	def getFirstDoiID (self):
		# Purpose: return the first DOI ID from the PDF file
		# Returns: string DOI ID or None (if no ID can be found)
		# Throws: Exception if this library has not been properly
		#	initialized or if there are errors in parsing the file

		self._loadFullText()
		if self.fullText:
			match = DOI_RE.search(self.fullText)
			if match:
				doiID = match.group(1)

				slash = doiID.find('/')
				nl = doiID.find('\n')

				# special case for PLoS journals, which often
				# have a line break in the ID

				if doiID.startswith('10.1371/') and \
					(0 < nl < 17):
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

				# if this is a Blood DOI ID, the hypenation 
				# sometimes needs tweaking

				match = BLOOD_DOI_RE.match(doiID)
				if match:
					numbers = match.group(1)
					revised = hyphenate(numbers)
					doiID = doiID.replace(numbers, revised)

				return doiID
		return None

	def getText (self):
		# Purpose: return the full text extracted from the PDF file
		# Returns: string (full text)

		self._loadFullText()
		if self.fullText:
			return self.fullText
		return None
