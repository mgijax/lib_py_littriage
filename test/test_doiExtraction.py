#!/usr/local/bin/python

import sys
import unittest
import os
import os.path
import PdfParser

"""
These are tests for PdfParser.py, specifically for getFirstDoiID() method.

Usage:   test_doiExtraction.py [-v]

One test_xxx() method per pdf. Try to cover all the individual cases
    for each journal that has special handling and any other weird cases.
    PDF files live in the pdfs/ subdirectory.

    The test methods, in effect, also describe the individual pdf files.

When running this, be careful of these environment variables:
    LITPARSER - Make sure it points to the litparser product you want to test
    MGICONFIG - This affects PDFTOTEXT path used in litparser
    PYTHONPATH - Most likely, you want .:.. at the start of your PYTHONPATH,
            otherwise, you end up testing PdfParser.py in /usr/local/mgi/live
            depending on where you run this script from.
"""

LITPARSER = os.environ.get('LITPARSER','/usr/local/mgi/live/mgiutils/litparser')
PdfParser.setLitParserDir(LITPARSER)

PDF_SUBDIR = "pdfs"     # name of the subdirectory holding the test PDFs
def getAbsolutePdfPath(pdfFile):
    """ determine absolute path to pdf test file """
    testDir = os.path.dirname(os.path.abspath(sys.argv[0]))     # test directory
    return os.path.abspath(os.path.join(testDir, PDF_SUBDIR, pdfFile))

###########################
class TestDoiExtraction(unittest.TestCase):
    def _getDoiID(self, pdfFile):
        """
        Get the DOI ID for the pdfFile.
        """
        self.pdfParser = PdfParser.PdfParser(getAbsolutePdfPath(pdfFile))
        id =  self.pdfParser.getFirstDoiID()
        return id

    def _getDoiID2(self, *args):
        """
        Get the DOI ID for the pdfFile, passing pdfFile as an arg tuple.
        Was trying to get this to work to use self.assertRaises() for tests
            that should raise an exception.
        It does work, however self.pdfParser is not accessible after the
            exception. Not sure why. Some subtlety to unittest.TestCase class?
            I wanted it so I could evaluate self.pdfParser.getStderr()
        """
        (pdfFile) = args
        return self._getDoiID(pdfFile)

    ###########################
    # Tests
    ###########################
    def test_jci_insight_splitID(self):
        # jci_insight w/ DOI split across lines: '10.1172/jci.\ninsight.95456'
        self.assertEqual(self._getDoiID('6407572_J287562.pdf'),
                                                '10.1172/jci.insight.95456')
    def test_jci_insight_nosplit(self):
        # jci_insight w/ DOI on one line: '10.1172/jci.insight.85888'
        # Should work after 13312 fix.
        self.assertEqual(self._getDoiID('27358912.pdf'),
                                                '10.1172/jci.insight.85888')
    def test_sage_just_digits(self):
        # Sage journal Toxicol Pathol, just digits in doi. No trailing '.'
        # '10.1177/0192623312438736'
        self.assertEqual(self._getDoiID('5803789_J235853.pdf'),
                                                '10.1177/0192623312438736')
    def test_sage_digits_dot(self):
        # Sage journal J Dent Res, digits in doi followed by '.'
        # '10.1177/0022034514527971.'
        self.assertEqual(self._getDoiID('5586774_J213878.pdf'),
                                                '10.1177/0022034514527971')
    def test_sage_with_Journal(self):
        # Sage journal J Dent Res, with "Journal" following digits in 1st doi
        # '10.1177/0022034515573273Journal'
        self.assertEqual(self._getDoiID('5816706_J237759.pdf'),
                                                '10.1177/0022034515573273')
#    def test_sage_with_JOURNAL(self):
#        # Sage journal J Biol Rhythms, w/ "JOURNAL" following digits in 1st doi
#        # '10.1177/0748730414561545JOURNAL'
#        # not sure how prevalent this case is, may not be worth testing for
#        self.assertEqual(self._getDoiID('5792796_J235116.pdf'),
#                                                '10.1177/0748730414561545')
    def test_PNAS_with_slash(self):
        # PNAS, has slash: '10.1073/pnas.1915658117'
        self.assertEqual(self._getDoiID('MGI_6388730.pdf'),
                                                '10.1073/pnas.1915658117')
    def test_PNAS_no_slash(self):
        # PNAS, slash is lost in extracted text: '10.1073pnas.041475098'
        self.assertEqual(self._getDoiID('MGI_1930716.pdf'),
                                                '10.1073/pnas.041475098')
    def test_PNAS_no_slash_trailing_dot(self):
        # PNAS, no slash. Has trailing '.':  '10.1073pnas.080517697.'
        # 6/10/2020: stripping trailing '.' doesn't seem to be handled anymore,
        #            so this test fails.
        self.assertEqual(self._getDoiID('MGI_1334476.pdf'),
                                                '10.1073/pnas.080517697')
    def test_PNAS_DCSupplemental(self):
        # PNAS, with DCSupplemental (TR 13224)
        # first doi in text is '10.1073/pnas.1902537116/-/DCSupplemental.'
        self.assertEqual(self._getDoiID('MGI_6381215.pdf'),
                                                '10.1073/pnas.1902537116')
    def test_PLOS_nospace(self):
        # PLOS journal w/ no space in 1st doi occurrance:
        #      '10.1371/journal.pone.0224646'
        self.assertEqual(self._getDoiID('MGI_6385447.pdf'),
                                                '10.1371/journal.pone.0224646')
    def test_PLOS_with_space1(self):
        # PLOS journal w/ a space in 1st doi occurrance (due to line break)
        #      '10.1371/journal. pone.0226785'
        self.assertEqual(self._getDoiID('MGI_6385476.pdf'),
                                                '10.1371/journal.pone.0226785')
    def test_PLOS_with_space2(self):
        # PLOS journal w/ a space in 1st doi occurrance (due to line break)
        #      '10.1371/ journal.pone.0226931'
        self.assertEqual(self._getDoiID('MGI_6385484.pdf'),
                                                '10.1371/journal.pone.0226931')
    def test_locked_pdf(self):
        """ test PDF that is password protected so pdftotext won't open it.
            Should get exception and correct stderr msg.
            (although we'd prefer if we could coax pdftotext to open these)
        """
        # Could do this to just test for the exception:
        #    self.assertRaises(Exception, self._getDoiID2, '6378478.pdf' )
        # (took me a while to figure this out, so I'm leaving the comment here)
        # (might retry this in python3. Can use:   with self.assertRaises... )

        pdfFile = '6378478.pdf'
        msg = "Permission Error: Copying of text from this document is not allowed.\n"
        try:
            pdfParser = PdfParser.PdfParser(getAbsolutePdfPath(pdfFile))
            id = pdfParser.getFirstDoiID()
        except Exception:
            errmsg = pdfParser.getStderr()
            self.assertEqual(errmsg, msg)
        else:
            self.fail(msg="Did not get exception on pdftotext Permission Error")

    def test_invalid_pdf(self):
        """ test invalid PDF file.
            Should get exception and correct stderr msg.
        """
        pdfFile = 'isInvalid.pdf'
        msg = "Syntax Warning: May not be a PDF file (continuing anyway)"
        try:
            pdfParser = PdfParser.PdfParser(getAbsolutePdfPath(pdfFile))
            id = pdfParser.getFirstDoiID()
        except Exception:
            errmsg = pdfParser.getStderr()
            self.assertTrue(errmsg.startswith(msg),
                                            "Wrong pdftotext error message")
        else:
            self.fail(msg="Did not get exception on invalid PDF file.")
# end class TestDoiExtraction -------------------

if __name__ == '__main__':
    unittest.main()
