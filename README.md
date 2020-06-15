# lib_py_littriage
Contains libraries necessary for literature triage, supporting relevant data loads and curatorial interfaces.

## PdfParser.py

This module provides the PdfParser class, which wraps up the logic for parsing text out of a PDF file and providing easy access to it.

The module must be initialized by calling setLitParserDir() with the path to the litparser (https://github.com/mgijax/litparser) product installation.

After the module has been initialized, you may...

* instantiate a PdfParser object by passing in the path to a PDF file
* ask the PdfParser to return the DOI ID in the file (getFirstDoiID)
* ask the PdfParser for the full text from the file (getText)

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

### testPMA_getPubMedIDs.py
Is an adhoc test that exercises PubMedAgent.getPubMedIDs() in PubMedAgent.py

### testPMA_getReferences.py
Is an adhoc test that exercises PubMedAgentMedline.getReferences() in PubMedAgent.py
