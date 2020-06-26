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

    PDF file naming note: many are named after the MGI ID of the reference but
        with "MGI_nnnnnn" format (instead of ":"). I found the ":" in the file
        names messed up bash's file completion mechanism.

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
        # currently errors: Should work after TR 13312 fix.
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
    def test_Science_1st_DOI_ok(self):
        # Science w/ 1st doi occurrance actually ok: '10.1126/science.1179438'
        #   (plus intervening other DOI's in text & has supp data)
        self.assertEqual(self._getDoiID('MGI_4417979.pdf'),
                                                '10.1126/science.1179438')
    def test_Science_1st_DOI_ok2(self):
        # Science (recent 2019) '10.1126/science.aav0581'
        #   (plus intervening other DOI's in text & has supp data)
        self.assertEqual(self._getDoiID('MGI_6280790.pdf'),
                                                '10.1126/science.aav0581')
    def test_Science_1st_not_ok(self):
        # Science w/ 1st doi wrong: '10.1126/science.1179802'
        #  correct: '10.1126/science.1180067' appears later
        #   (plus intervening other DOI's in text & has supp data)
        self.assertEqual(self._getDoiID('MGI_4429730.pdf'),
                                                '10.1126/science.1180067')
    def test_Sci_Signal(self):
        # Sci Signal w/ good ID multiple times: '10.1126/scisignal.aah4598'
        self.assertEqual(self._getDoiID('MGI_5913802.pdf'),
                                                '10.1126/scisignal.aah4598')
    def test_Blood_reg_article1(self):
        # Blood, regular article. 1st ID instance is split
        # '10.1182/\nblood-2018-05-851667.' and has trailing '.'
        self.assertEqual(self._getDoiID('MGI_6284584.pdf'),
                                                '10.1182/blood-2018-05-851667')
    def test_Blood_reg_article2(self):
        # Blood, regular article. Needs hyphenation cleanup from extracted text
        # Appears in ext text as: '10.1182/blood2018-07-861237.'
        # 6/25/2020: currently fails, doesn't fix hyphenation
        self.assertEqual(self._getDoiID('MGI_6284913.pdf'),
                                                '10.1182/blood-2018-07-861237')
    def test_Blood_reg_article3(self):
        # Blood, regular article. Needs hyphenation cleanup from extracted text
        # Appears in ext text as: '10.1182/blood-201807-864538.'
        # 6/25/2020: currently fails, doesn't fix hyphenation
        self.assertEqual(self._getDoiID('MGI_6306196.pdf'),
                                                '10.1182/blood-2018-07-864538')
    def test_Blood_comment_article1(self):
        # Blood, comment article. 1st ID instance is for previous paper in PDF
        # '10.1182/blood-2018-12-891481' 
        # 6/25/2020: currently this fails as it gets the above ID.
        # This reference has been deleted from the db.
        self.assertEqual(self._getDoiID('MGI_6284574.pdf'),
                                                '10.1182/blood-2018-12-889758')
    def test_Blood_comment_article2(self):
        # Blood, comment article. This is 1st comment article (so no prev one)
        # ID is clean, not split, not missing any chars.
        self.assertEqual(self._getDoiID('MGI_6284696.pdf'),
                                                '10.1182/blood-2018-12-889766')
    def test_eLife_extra_digits(self):
        # eLife, 1st doi has extra digits: '10.7554/eLife.41156.001'
        self.assertEqual(self._getDoiID('MGI_6304063.pdf'),
                                                '10.7554/eLife.41156')
    def test_eLife_no_extra_digits(self):
        # eLife, 1st doi has no extra digits: '10.7554/eLife.47985'
        self.assertEqual(self._getDoiID('MGI_6304087.pdf'),
                                                '10.7554/eLife.47985')
    def test_eLife_no_extra_digits_but(self):
        # eLife, 1st doi has no extra digits: '10.7554/eLife.46279'
        # but has link to related article DOI before this article DOI.
        self.assertEqual(self._getDoiID('MGI_6304117.pdf'),
                                                '10.7554/eLife.46279')
    def test_Reproduction_no_spaces(self):
        # Reproduction, no spaces in the 1st ID: '10.1530/REP-19-0022'
        self.assertEqual(self._getDoiID('MGI_6392665.pdf'),
                                                '10.1530/REP-19-0022')
    def test_Reproduction_spaces(self):
        # Reproduction, spaces in the 1st ID: '10.1530/REP -18-0366'
        self.assertEqual(self._getDoiID('MGI_6393822.pdf'),
                                                '10.1530/REP-18-0366')
    def test_Reproduction_older_paper(self):
        # Reproduction, no spaces in the 1st ID, but older, no 'doi.org/':
        # 'DOI: 10.1530/REP-16-0231'
        # 6/26/2020: currently errors since code expects 'doi.org/'
        self.assertEqual(self._getDoiID('MGI_5823517.pdf'),
                                                '10.1530/REP-16-0231')
    def test_ASM_no_breaks(self):       # Amer Soc for Microbiology
        # J Virol: no line break or space in 1st doi: '10.1128/JVI.01806-18.'
        # (but trailing '.')
        self.assertEqual(self._getDoiID('MGI_6286560.pdf'),
                                                '10.1128/JVI.01806-18')
    def test_ASM_break1(self):       # Amer Soc for Microbiology
        # J Virol: line break in 1st doi: '10.1128/JVI\n.01173-18.'
        # (but trailing '.')
        # 6/26/2020: currently fails as pdftotext inserts ' ' instead of '\n'
        #   and code is only handling '\n'
        self.assertEqual(self._getDoiID('MGI_6342319.pdf'),
                                                '10.1128/JVI.01173-18')
    def test_ASM_break2(self):       # Amer Soc for Microbiology
        # mBio: line break in 1st doi: '10.1128/\nmBio.01065-19'
        # (but trailing '.')
        # 6/26/2020: probably is matching 2nd DOI in the PDF which is correct
        self.assertEqual(self._getDoiID('MGI_6391745.pdf'),
                                                '10.1128/mBio.01065-19')
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
