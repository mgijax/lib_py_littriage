# lib_py_littriage
Contains libraries necessary for literature triage, supporting relevant data loads and curatorial interfaces.

## PdfParser.py
This module provides the PdfParser class, which wraps up the logic for parsing text out of a PDF file and providing easy access to it.

The module must be initialized by calling setLitParserDir() with the path to the litparser (https://github.com/mgijax/litparser) product installation.

After the module has been initialized, you may...

* instantiate a PdfParser object by passing in the path to a PDF file
* ask the PdfParser to return the DOI ID in the file (getFirstDoiID)
* ask the PdfParser for the full text from the file (getText)

## ExtractedTextSet.py
This module provides utilities for recovering the extracted text for 
references (bib\_refs records) in the database.

Extracted text is stored in the bib\_workflow\_data table in the database,
but it is stored split into sections (body, references, supplemental, ...),
and it is not so easy to recover the full text concatenated back together.

The ExtractedTextSet class defined here does this for you.

Convenience functions for building an ExtractedTextSet for a set of
\_refs\_keys are also provided.

If run as a script, this module takes a \_ref\_key as a cmd line argument
and writes the (full) extracted text for the reference to stdout.
See ExtractedTextSet.py -h

## extractedTextSplitter.py
Module for splitting the extracted text of articles into sections.
TR 12763

The sections we split into (in relative order):
    body                - everything up to the next section
    references          - the reference section
    manuscript figures  - some manuscript PDFs have figures/tables after
                           the refs
                          (WE USE THE TERM "figure" to mean "figure/table" )
    star*methods        - some papers have an extended "methods" section
                           after the refs. This section is called "Star*Methods"
    supplemental data   - indicated by a special MGI text tag inserted by
                           Nancy or someone in MGI when the supp data is added
                           to the PDF

## Testing
See test/ subdirectory.

When running these scripts, be aware of your PYTHONPATH and LITPARSER settings.
You may be exercising python modules in /usr/local/mgi/live instead of your
dev directories (which may be what you want).

### PdfParser.py DOI ID extraction
`test_doiExtraction.py -v` runs automated tests using the python unittest
framework.

Also serves as the index describing which pdfs are for which journals with
which flavors of DOI formatting.
The pdfs are in the pdfs/ subdirectory.

`getDOI.py <pdffile or MGI:nnn>` extracts the DOI ID from the specified file
for a quick manual test.

If you pass it an MGIid of an article, it extracts the DOI ID from the pdf
in our pdf storage. It also prints the path to that pdf so you can grab it
if you want it as an example.

`findDoiExamples.py <doi prefix>` helps you find example pdfs in the database.

For example, `findDoiExamples.py 10.1073` prints snippets of extracted text
that contain DIO IDs from PNAS articles. This lets you find examples of the 
different ways DOI IDs may be formatted in PNAS. (Note this script is looking
at the extracted text in the database, not any pdfs.)

When looking for examples, be aware that Nancy has manually added the DOI ID at
the beginning of some pdfs (and thus to our extracted text). So the pdfs in our
storage may not always be the same as the raw pdf from the journal/publisher.

See `findDoiExamples.py -h` for various options
(e.g., look by publication year).

### doiRetry.py
`doiRetry.py` re-extracts DOI IDs for papers already in the db and compares
those IDs with the DOI ID for each paper in the accession table.

You can use this to test how changes to PdfParser.py would affect papers whose
DOI IDs we already know.

`doiRetry.py -h` gives you many different options. One option uses the extracted
text that is already stored in the db (this is fast), another option uses
pdftotext to re-extract the text from PDFs stored in our pdf storage (slow).

### testPMA_getPubMedIDs.py
Is an adhoc test that exercises PubMedAgent.getPubMedIDs() in PubMedAgent.py

### testPMA_getReferences.py
Is an adhoc test that exercises PubMedAgentMedline.getReferences() in PubMedAgent.py
