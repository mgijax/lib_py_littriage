# lib_py_littriage
Contains libraries necessary for literature triage, supporting relevant data loads and curatorial interfaces.

## PdfParser.py

This module provides the PdfParser class, which wraps up the logic for parsing text out of a PDF file and providing easy access to it.

The module must be initialized by calling setLitParserDir() with the path to the litparser (https://github.com/mgijax/litparser) product installation.

After the module has been initialized, you may...

* instantiate a PdfParser object by passing in the path to a PDF file
* ask the PdfParser to return the first DOI ID in the file (getFirstDoiID)
* ask the PdfParser for the full text from the file (getText)

