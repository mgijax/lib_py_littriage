"""
###################
Module for splitting the extracted text of articles into sections.
TR 12763

This code should work in python2.4 and 2.7

Author: Jim

This section detection from extracted text is not an exact science.
So we consider these section boundaries to be PREDICTIONS.
They will be wrong sometimes.

###################
The sections we split into (in relative order):
    body		- everything up to the next section
    references		- the reference section
    manuscript figures	- some manuscript PDFs have figures/tables after
                           the refs
                          (WE USE THE TERM "figure" to mean "figure/table" )
    star*methods	- some papers have an extended "methods" section
                           after the refs. This section is called "Star*Methods"
    supplemental data	- indicated by a special MGI text tag inserted by
                           Nancy or someone in MGI when the supp data is added
                           to the PDF

The end of each section is the beginning of the next section.

The start and end of each section is represented as 
    sPos - index (in the extracted text) of the 1st char of the section
    ePos - index of 1st char NOT in the section

    So if a section ends at the end of the extracted text, ePos = len(extText).
    extText[ePos:ePos] is the text of the section.

Any section can be empty, in which case, its sPos and ePos are the sPos of
the next section

###################
Basic usage:
###################

    splitter = ExtTextSplitter()

    # To just get the actual sections' str.

    (body, refs, manuFigures, starMethods, suppData) = \
                                                splitter.splitSections(text)

    # To get Section objects that contain more info about each predicted section
    # (Section Objects contain: type, text, sPos, ePos, and a "reason" the
    #   splitting algorithm made its prediction - see Section Class below):

    (bodyS, refsS, manuFiguresS, starMethodsS, suppDataS) = \
                                                splitter.findSections(text)
###################
Overview of the Splitting Algorithm:
###################

Search backward for the MGI supplemental data tag
Search backward from there for Star Methods
Search backward from there for References start
If Refs start is found, search for Manuscript figures: search foward from
    there for a figure legend occurring before the start of Star Methods
    NOTE this will match any figure/table legend after the start of the refs,
        even if they are not in an official "manuscript" section.
        But ending the refs section at any legend is good
Body = start of text up to References start

There are also minFraction (for all sections) and maxFraction (for references
section) -- JIM need to discuss

Remember if we don't predict a section, it is set to the start of the next
section.
For example, if we don't find a Refs section start, it (and the Manu Figs)
    sPos == Star*methods sPos
    which may == Supp data sPos
    which may == end of extracted text.

Algorithm approach:
You cannot search backward in a str.with a regex.
Instead, we put all the different section heading patterns into one honking
regex that we match (forward) against the extText.
(so we only make one pass through the str.
Then we can scan the list of all regex matches backward (or forward) as neededj.
See class TypedRegexMatcher


###################
Overview of Classes
###################
class Section		- describes a section
class ExtTextSplitter	- implements the splitting algorithm
class TypedRegexMatcher	- takes regex's grouped by user defined "type",
                            combines them, lets you match against a str.
                            and gives you back lists of TypedMatch objects
                            that represent the matches found
class TypedMatch	- describes a match from TypedRegexMatcher
"""

import re

# ----------------------------------
#  Regex building functions
# ----------------------------------
def spacedOutRegex(s):
    # for given str. return regex pattern str.that matches the chars
    #  in the str.with optional spaces between the chars.
    # Useful because sometimes the PDF to text extraction inserts spaces.
    reg = []
    for c in s:
        reg.append('[%s]' % c)
    return '[ ]*'.join(reg)

#-----------------------------------------------
# Section type names:
SECTION_BODY  = 'body'
SECTION_REFS  = 'references'
SECTION_MFIGS = 'manuscript figures'
SECTION_STAR  = 'star methods'
SECTION_SUPP  = 'supplemental data'
# other constants
SUPP_DATA_TAG = "MGI Lit Triage Supplemental Data"
PARA_BOUNDARY = '\n\n'	# paragraph boundary chars that are in ext text
#-----------------------------------------------

class Section (object):
    """
    IS an object that describes a section of an article (from extracted text)
    """
    def __init__(self, secType, text='', reason='', sPos=None, ePos=None):
        self.secType = secType	# section name. see vocab above
        self.text    = text	# the text of the section
        self.reason  = reason	# reason this section start was chosen
                                #  typically the str.that we matched
                                #  for section header.
        self.sPos    = sPos	# start position within the article text
        self.ePos    = ePos	# end pos - index of 1st char not in section

    def __str__(self):
        return "Section object: %s reason: '%s' %d %d\n'%s'\n" %  \
            (self.secType, self.reason, self.sPos, self.ePos, self.text[:40])
#------------------ end Class SectionBoundary

class ExtTextSplitter (object): #{
    '''
    Is: a class that knows how to split extracted text for a PDF
        into multiple parts:
            body, references, manuscript figs, "star methods", supp data
            (any of these sections except body can be the empty str.
            "Star Methods" is a methods section that some journals put after
            the references and before any supplemental data.

    Has: floats: minFraction, maxFraction and a TypedRegexMatcher

        The min/maxFractions are used ... JIM: doc this better
        once any supp data and "star methods" section are removed from the end
        of the text.
        If the length of the predicted reference section is
            > maxFraction of the total text length from the end
            or
            < minFraction from the end
        then the prediction is considered invalid, and the reference section
        is set to '', and the body is not split.

    Does: splitSections() - get the section str.
           findSections() - get descriptions of the section
    '''

    # Names of the match/regex types
    REF_SECTION_PRIMARY   = 'refSection1'
    REF_SECTION_SECONDARY = 'refSection2'
    MANUSCRIPT_FIGURES	  = 'manuFigures'
    STAR_METHODS          = 'starMethods'
    SUPP_DATA             = 'suppData'

    # Regex pattern for optional figure legend start
    # Different journals/articles may have words before "Figure":
    #   any single word, "\w+",  or the specific word combos below
    OPT_FIG_START = r'(?:(?:\w+'                                  + \
                    '|' + spacedOutRegex('supp data')          + \
                    '|' + spacedOutRegex('supplemental data')  + \
                    '|' + spacedOutRegex('supplementary data') + \
                    '|' + spacedOutRegex('extended data')      + \
                    r') )?'

    # Dict defining all the section start tags and their match types
    # End each w/ \n or \b to force line or word boundaries
    # The startPattern on TypedRegexMatcher constructor sets '\n' for line start
    regexDict = {
        REF_SECTION_PRIMARY  : [spacedOutRegex("References")            + '\n',
                                spacedOutRegex("Literature Cited")      + '\n',
                                spacedOutRegex("References and Notes")  + '\n',
                                ],
        REF_SECTION_SECONDARY: [spacedOutRegex("Reference")             + '\n',
                                spacedOutRegex("Acknowledgements")      + r'\b',
                                spacedOutRegex("Acknowledgments")       + r'\b',
                                spacedOutRegex("Conflicts of Interest") + r'\b',
                                spacedOutRegex("Conflict of Interest")  + r'\b',
                                ],
        MANUSCRIPT_FIGURES   : [OPT_FIG_START + spacedOutRegex("Figure")+ r'\b',
                                OPT_FIG_START + spacedOutRegex("Fig")   + r'\b',
                                OPT_FIG_START + spacedOutRegex("Table") + r'\b',
                                ],
        STAR_METHODS         : [spacedOutRegex("Star") + "[ ]*[ *+][ ]*" +
                                            spacedOutRegex("Methods") + '\n',
                                ],
        SUPP_DATA            : [spacedOutRegex(SUPP_DATA_TAG) + '\n',
                                ],
                }

    def __init__(self,
                minFraction=0.05, # min fraction predicted for ref section
                maxFraction=0.4,  # max fraction of whole doc that the
                                  #  predicted ref section is allowed to be
        ):
        self.minFraction = minFraction
        self.maxFraction = maxFraction
        self.matcher = TypedRegexMatcher(self.regexDict, startPattern='\n')
        self.initSections('')
    # ----------------------------------

    def getRegexMatcher(self):	return self.matcher
    def getExtText(self): 	return self.extText
    # ----------------------------------

    def initSections(self, extText):
        """
        initialize all the text sections to missing
        """
        self.extText = extText
        self.lenExtText = len(extText)

        # body is whole thing for now.
        self.bodyS = Section(SECTION_BODY, extText, "body start", 0,
                                                            self.lenExtText)

        # mark all other sections as missing for now
        self.refsS = Section(SECTION_REFS,  '', 'no ref section match',
                                            self.lenExtText, self.lenExtText)
        self.mfigS = Section(SECTION_MFIGS, '', 'no manuscript figs match',
                                            self.lenExtText, self.lenExtText)
        self.starS = Section(SECTION_STAR,  '', 'no star methods match',
                                            self.lenExtText, self.lenExtText)
        self.suppS = Section(SECTION_SUPP,  '', 'no supp data match',
                                            self.lenExtText, self.lenExtText)
    # ----------------------------------

    def splitSections(self, extText):
        """
        #### if you just want the text of the sections, call this ####
        Split the exText, return the sections text
        Return the text of the sections tuple:
            (body, ref section, manuscript figs, star methods, supp data)
        """
        self.findSections(extText)
        return (self.bodyS.text,
                self.refsS.text,
                self.mfigS.text,
                self.starS.text,
                self.suppS.text,
                )
    # ----------------------------------

    def findSections(self, extText):
        """
        #### if you want details of the sections, call this ####
        Find the sections in text.
        Set self.bodyS, refsS, mfigS, starS, suppS
            to Section objects describing each section
        Return the 5 Section objects:
        """
        self.initSections(extText)

        matches = self.matcher.match(extText)
        if len(matches) != 0:		# got some matches
            # The order of these calls is important
            self.findSuppSection()
            self.findStarSection()
            self.findRefsSection()
            self.findMfigSection()
            self.findBodySection()
        return self.bodyS, self.refsS, self.mfigS, self.starS, self.suppS
    # ----------------------------------

    def findSuppSection(self):
        """
        Set self.suppS
        Assumes:
            self.suppS is initialized to be length 0 at end of self.extText
        """
        section = self.suppS
        matches = self.matcher.getMatches(self.SUPP_DATA)
        if len(matches) != 0:		# matched supp data start tags
            m = matches[-1]		# use last match

            section.reason = m.text
            section.sPos   = m.sPos
            section.ePos   = self.lenExtText
            section.text   = self.extText[section.sPos : section.ePos]

        # else assume self.suppS is already initialized correctly
        return
    # ----------------------------------

    def findStarSection(self):
        """
        Set self.starS
        Assumes:
            self.suppS is set appropriately
            self.starS is initialized to be length 0 at end of self.extText
        """
        section = self.starS
        allMatches = self.matcher.getMatches(self.STAR_METHODS)

        matches = []
        for m in allMatches:	# collect matches before supp data start
            if m.sPos < self.suppS.sPos: matches.append(m)
            else: break

        if len(matches) == 0:		# no star methods match
            section.sPos = self.suppS.sPos
            section.ePos = self.suppS.sPos
        else:				# got a match
            matches.reverse()
            m = self.findNotTooLateMatch(matches)
            if m == None:			# no reasonable match
                section.reason = 'star methods too close to end (%d)' % \
                                                            matches[-1].sPos
                section.sPos = self.suppS.sPos
                section.ePos = self.suppS.sPos
            else:			# got a good one
                section.reason = m.text
                section.sPos   = m.sPos
                section.ePos   = self.suppS.sPos

        section.text   = self.extText[section.sPos : section.ePos]
        return
    # ----------------------------------

    def findRefsSection(self):
        """
        Set self.refsS
        Assumes:
            self.starS is set appropriately
            self.refsS is initialized to be length 0 at end of self.extText
        """
        section   = self.refsS
        primary   = self.matcher.getMatches(self.REF_SECTION_PRIMARY)
        secondary = self.matcher.getMatches(self.REF_SECTION_SECONDARY)

        m, primaryReason = self.findRefsMatch(primary)

        if m:				# got a good primary match
            section.reason = primaryReason
            section.sPos   = m.sPos
            section.ePos   = self.starS.sPos

        elif len(secondary) == 0:	# no good primary, and no secondary
            section.reason = primaryReason
            section.sPos   = self.starS.sPos
            section.ePos   = self.starS.sPos
        else:				# no good primary, but some secondary
            m, secondaryReason = self.findRefsMatch(secondary)

            if m:			# got good secondary match
                section.reason = secondaryReason
                section.sPos   = m.sPos
                section.ePos   = self.starS.sPos
            else:			# no good secondary match either
                section.reason = primaryReason + '; \n' + secondaryReason
                section.sPos   = self.starS.sPos
                section.ePos   = self.starS.sPos

        section.text   = self.extText[section.sPos : section.ePos]
        return
    # ----------------------------------

    def findRefsMatch(self, allMatches):
        """
        Find a good match in 'allMatches'.
        Return the good match object (or None) + reason
        Assumes: matches is sorted from start of doc to end
        """
        matches = []
        for m in allMatches:	# collect matches before star methods start
            if m.sPos < self.starS.sPos: matches.append(m)
            else: break

        if len(matches) != 0:		# matched refs start tags
            matches.reverse()		# find last occurances first
            m = self.findNotTooLateMatch(matches)
            if m != None:		# match that is not too late

                # is length of refs too big?
                refLength = self.starS.sPos - m.sPos
                if float(refLength)/float(self.starS.sPos) <= self.maxFraction:
                    reason = m.text
                else:			# refs section too big
                    reason = "refs match is too early: '%s' (%d)" % \
                                                            (m.text, m.sPos)
                    m = None
            else:			# no good match
                reason ="refs matches too close to end, earliest: '%s' (%d)" % \
                                        (matches[-1].text, matches[-1].sPos)
                m = None
        else:				# no start tag found
            m = None
            reason = 'no refs match'

        return m, reason
    # ----------------------------------

    def findMfigSection(self):
        """
        Look forward from refs section to star methods & see if any
        figures/tables in between. 
        If so, truncate refs section at first figure/table start.
        set the mfigS to be the fig start to star methods start.
        Assume:
            self.starS is set appropriately
            self.mfigS is initialized to be length 0 at end of self.extText
        """
        section = self.mfigS
        matches   = self.matcher.getMatches(self.MANUSCRIPT_FIGURES)

        figMatch = None		# the match of the 1st fig after refs start
        for m in matches:
            if self.refsS.sPos < m.sPos and m.sPos < self.starS.sPos:
                figMatch = m
                break
        if figMatch:		# got a fig after refs & before any starS
            section.reason  = figMatch.text
            section.sPos    = figMatch.sPos
            section.ePos    = self.starS.sPos
            section.text    = self.extText[section.sPos : section.ePos]

            self.refsS.ePos = figMatch.sPos	# adjust end of refs section
            self.refsS.text = self.extText[self.refsS.sPos: self.refsS.ePos]
        else:			# no fig match
            section.sPos = self.starS.sPos
            section.ePos = self.starS.sPos
            # section.text & reason should be set ok from initSections
        return
    # ----------------------------------

    def findBodySection(self):
        section = self.bodyS
        section.sPos = 0
        section.ePos = self.refsS.sPos
        section.text = self.extText[section.sPos : section.ePos]
        return
    # ----------------------------------

    def findNotTooLateMatch(self, matches, totalTextLength='default'):
        """
        Given a list of matches, return the 1st one that is not too close
        to the end.
          (at least self.minFactor from textEnd JIM: doc better)
        Return None if we don't find one
        """
        if totalTextLength == 'default': totalTextLength = self.lenExtText
        retVal = None
        for m in matches:
            if not self.isTooCloseToEnd(m.sPos, totalTextLength):
                retVal = m
                break
        return retVal
    # ----------------------------------

    def isTooCloseToEnd(self, sPos, totalTextLength='default'):
        """
        Return Boolean: Is the predicted (section) start position too
        close to the end to be reasonable?

        (if too close, it is likely some text in the PDF page footer)
        """
        if totalTextLength == 'default': totalTextLength = self.lenExtText
        sectionLen = totalTextLength - sPos
        sectionLengthFraction = float(sectionLen)/totalTextLength
        return sectionLengthFraction < self.minFraction
    # ----------------------------------

#------------------ end Class ExtTextSplitter }


class TypedMatch (object):
    """
    Represents a match from a TypedRegexMatcher.
    """
    def __init__(self, matchType, text, sPos, ePos):
        self.matchType = matchType	# types from the regexDict passed
                                        #  to TypedRegexMatcher
        self.text      = text		# the str.that matched the regex
        self.sPos      = sPos		# start pos in the text of matching str
        self.ePos      = ePos		# end pos in the text of matching str
                                        #  i.e., 1st index in text after match

    def __str__(self):
        return "TypedMatched object: %s '%s' %d %d" %  \
                            (self.matchType, self.text, self.sPos, self.ePos)
#-----------------------------------------------

class TypedRegexMatcher (object): #{
    """
    Is: A class that matches a set of regex's against str..
        Each regex has a user defined type/category name.
        Once you have matched against a str. you can get back the matches
        by type, in the order the matches occur in the str.

        This is built to make one regex match pass over a str.once, and
        yet pull out all the individual matches, by type.

    Has: Dict of typed regex's:
            {'type 1' : [regex pattern str....],
             'type 2' : [regex pattern str....],
             ...
            }
         A honking regex built from this dict
    Does: match('sometext')
          After a match:
              getMatches('type'), getAllMatches()
              return lists of TypedMatch objects in the order they appear
              in 'sometext'
    """
    # -----------------------

    def __init__(self,
                 regexDict,		# Dict of regex's as above
                 startPattern='',	# Regex pattern str to match at the
                                        #  start of all regex's. 
                                        # Use this to force matches at start
                                        #  of paragraphs.
                 flags=re.IGNORECASE,	# Regex flags when matching, see re.
                                        #  flags=0 to get re module defaults
                ):
        self.regexDict    = regexDict
        self.regexTypes   = list(self.regexDict.keys())
        self.startPattern = startPattern
        self.flags        = flags

        self.buildRegexStr()
        self.regex        = re.compile(self.regexStr, self.flags)

        self.initMatchResults()
    # ----------------------------------

    def buildRegexStr(self):
        """
        Set self.refRegex to the honking regex...
        Each regex type is its own named regex group.
        """
        regexParts = []
        for tType,regList in list(self.regexDict.items()):
            rs = r'(?P<%s>%s)' % ( tType, '|'.join(regList) )
            regexParts.append(rs)

        self.regexStr = self.startPattern + '(?:' + '|'.join(regexParts) + ')'
    # ----------------------------------

    def initMatchResults(self):
        """
        Initialize matchesByType and allMatches to empty lists
        """
        self.matchesByType = {}
        for t in self.regexTypes:
            self.matchesByType[t] = []
        self.allMatches    = []
    # ----------------------------------

    def match(self, text):
        """
        Match the regex's against the text.
        Return the list of all matches (TypeMatch objects)
        """
        self.initMatchResults()

        for reM in self.regex.finditer(text):	# for the regex Match objects

            # for the named groups:
            # Note all named groups are in the groupdict,
            #   even if there is no match to that group
            for mType, mText in list(reM.groupdict().items()):
                if mText != None: break	# when we find group w/ a value,
                                        #  that is the matching group

            sPos, ePos = reM.span(mType)
            m = TypedMatch(mType, mText, sPos, ePos) # our own match object

            self.allMatches.append(m)
            self.matchesByType[mType].append(m)

        return self.allMatches
    # ----------------------------------

    def getMatches(self, regexType):
        if regexType not in self.regexTypes:
            raise KeyError("invalid match type '%s'" % regexType)
        return self.matchesByType[regexType]

    def getAllMatches(self): return self.allMatches
    def getRegexStr(self):   return self.regexStr
    def getRegex(self):      return self.regex
    def getRegexTypes(self): return self.regexTypes
    # ----------------------------------
#------------------ end Class TypedRegexMatcher }


# -----------------------
if __name__ == "__main__":	# some ad hoc tests

    print("Running ad hoc tests - modify these as needed")

    if False:		# TypedRegexMatcher tests
        PARA_BOUNDARY = '\n\n'
        regexDict = {
            'animal'  : [spacedOutRegex('duck'),
                        r'\bdog\b'],
            'tree'    : ['[oO]ak|fir', 'apple', 'beech',],
                     }
        #matcher = TypedRegexMatcher(regexDict, startPattern=PARA_BOUNDARY)
        matcher = TypedRegexMatcher(regexDict, )

        print(matcher.getRegexStr())

        s = 'the \n\ndu ck\n and DoG climbed an Oak tree'
        #s = 'no matches here tree'

        print(len(matcher.match(s)))
        for m in matcher.getAllMatches():
            print(str(m))
        print()

        for t in list(regexDict.keys()):
            print("%s:\n[" % t)
            for m in matcher.getMatches(t):
                print(str(m))
            print('] ------')
        #x = matcher.getMatches('foo') # test using invalid regex type

    if True:		# ExtTextSplitter tests
        def runSectionTest(sp, doc):
            print("--------- doc length: %d" % len(doc))
            (bodyS, refsS, mfigS, starS, suppS) = sp.findSections(doc)
            print(str(bodyS))
            print(str(refsS))
            print(str(mfigS))
            print(str(starS))
            print(str(suppS))
        # -------

#		PARA_BOUNDARY + 'References' + 	\
#		"\n1234567890" +			\
#		PARA_BOUNDARY + 'star*methods' + 	\
#		PARA_BOUNDARY + 'star*methods' + 	\
        doc = "1234567890" +				\
                '\nfigure 1: here is a legend' + 	\
                '\n' + 'references' + 			\
                "\n1234567890" +			\
                '\n' + 'conf  licts of int  erest' + 	\
                "\n1234567890" +			\
                '\nsupplementary data TABLE 2: here is a legend' + 	\
                "\n1234567890" +			\
                '\nfigure 3: here is a legend' + 	\
                "\n1234567890" +			\
                '\n' + 'star*methods' + 		\
                "\n1234567890" +			\
                '\n' + SUPP_DATA_TAG +			\
                "\n1234567890"				\
                '\n' + 'star*methods' + 		\
                "\n1234567890"
        #doc = open('6114980.txt', 'r').read()
        #doc = "1234567890" + PARA_BOUNDARY + 'foo' + "\n1234567890"
        sp = ExtTextSplitter(maxFraction=0.9, minFraction=.1)
        #print sp.getRegexMatcher().getRegexStr()
        runSectionTest(sp, doc)
