#!/usr/local/bin/python

# extTextSplitter.cgi
# CGI for generating a web page that supports curators looking at the
# how the extractedTextSplitter.py works for different references
# Curators enter pubmed ID and sees the results of the text section splitting

import sys
#import httpReader
import string
import cgi
import os
import os.path
# How to make this cgi work on bhmgidevapp01 ?
#sys.path.insert(0, '/home/jsb/jax/prod/lib/python')
#sys.path.insert(0, '/usr/local/lib/python2.4')
#sys.path.insert(0, '/usr/local/mgi/lib/python')
sys.path.insert(0, '/home/jak/lib/python/mgi')	# to find db module
import db
import runCommand
import extractedTextSplitter


def getReferenceInfo(pubmed):
    # Assumes we are working with a database schema that still has all the
    #   extracted text in one field:  bib_workflow_data.extractedText
    query = '''
    select a.accid pubmed, r.journal, r.title, bd.extractedtext
    from bib_refs r join bib_workflow_data bd on (r._refs_key = bd._refs_key)
	join acc_accession a on
	 (a._object_key = r._refs_key and a._logicaldb_key=29 -- pubmed
	  and a._mgitype_key=1 )
    where
    a.accid = '%s'
    ''' % str(pubmed)
    #--, translate(bd.extractedtext, E'\r', ' ') as "text" -- remove ^M's
    db.set_sqlServer  ('bhmgidevdb01')
    db.set_sqlDatabase('prod')
    db.set_sqlUser    ('mgd_public')
    db.set_sqlPassword('mgdpub')

    dbOutput = db.sql( string.split(query, '||'), 'auto')

    results = dbOutput[-1]	# list of results (should only be one)

    if len(results) == 0:
	return "PubMed ID '%s' not found" % str(pubmed)
    else:
	refInfo = results[0]
	refInfo['pdfLink'] = '<a href="http://bhmgiei01.jax.org/usrlocalmgi/live/pdfviewer/pdfviewer.cgi?id=%s" target="_blank">PDF</a>' % refInfo['pubmed']

	return refInfo
# ----------------------------

def getPDFfile(fileName):
    baseDir = '/mgi/all/wts_projects/12700/12763/Data_splitter_test/'

    refInfo = {}
    refInfo['pubmed'] = fileName
    refInfo['journal'] = 'from PDF'
    refInfo['title'] = 'from PDF'
    refInfo['pdfLink'] = '<a href="../Data_splitter_test/%s" target="_blank">PDF</a>' % fileName

    cmd = 'pdftotext -enc ASCII7 -q -nopgbrk %s -' % (baseDir + fileName)
    stdout, stderr, retcode = runCommand.runCommand(cmd) 
    if retcode != 0:
	refInfo = "retcode = %d<p>%s<p>%s<p>%s" % (retcode, cmd, stderr, stdout)
    else:
	refInfo['extractedtext'] = stdout

    return refInfo
# ----------------------------

def buildReferenceDetails(refInfo):
    splitter = extractedTextSplitter.ExtTextSplitter()
    #return 'debug: got here'

    bodyS, refsS, mfigS,  starS, suppS = splitter.findSections(refInfo['extractedtext'])
    reason = refsS.reason
    refStart = refsS.sPos
    lenText = len(refInfo['extractedtext'])
    #lenRefs = lenText - refStart
    #percent = 100 * float(lenRefs)/lenText

    textareaWidth = 150
    textareaHeight = 4
    pdfLink = refInfo['pdfLink']
    body = [
	'''
	<TABLE>
	<TR>
	    <TH>Link</TH>
	    <TH>PubMed/File</TH>
	    <TH>Journal</TH>
	    <TH>Title</TH>
	    <TH>Other</TH>
	</TR>
	<TR>
	''',
	    '<TD> %s </TD>' % pdfLink,
	    '<TD> %s </TD>' % refInfo['pubmed'],
	    '<TD> %s </TD>' % refInfo['journal'],
	    '<TD> %s </TD>' % refInfo['title'],
	'''
	    <TD>
		Doc length: %d
		<BR>Ref Section Matching Keyword: <B>%s</B>
	    </TD>
	'''	% (lenText, reason),
	'''
	<TR>
	</TABLE>
	''',
	'''
	<p>
	<b>Body</b> <small>%d to %d, %d chars</small>
	<BR>
	''' % (bodyS.sPos, bodyS.ePos, bodyS.ePos - bodyS.sPos),
	    '<textarea rows="%d" cols="%d">' % (textareaHeight, textareaWidth),
	     bodyS.text,
	    '</textarea>',
	'''
	<p>
	<b>Ref Section</b> <small>%d to %d, %d chars, Reason: "%s"</small>
	<BR>
	''' % (refsS.sPos, refsS.ePos, refsS.ePos - refsS.sPos, refsS.reason),
	    '<textarea rows="%d" cols="%d">' % (textareaHeight, textareaWidth),
	    refsS.text,
	    '</textarea>',
	'''
	<p>
	<b>Manuscript Figs  Section</b> <small>%d to %d, %d chars, Reason: "%s"</small>
	<BR>
	''' % (mfigS.sPos, mfigS.ePos, mfigS.ePos - mfigS.sPos, mfigS.reason),
	    '<textarea rows="%d" cols="%d">' % (textareaHeight, textareaWidth),
	    mfigS.text,
	    '</textarea>',
	'''
	<p>
	<b>Star Methods Section</b> <small>%d to %d, %d chars, Reason: "%s"</small>
	<BR>
	''' % (starS.sPos, starS.ePos, starS.ePos - starS.sPos, starS.reason),
	    '<textarea rows="%d" cols="%d">' % (textareaHeight, textareaWidth),
	    starS.text,
	    '</textarea>',
	'''
	<p>
	<b>Supplemental Data Section</b> <small>%d to %d, %d chars, Reason: "%s"</small>
	<BR>
	''' % (suppS.sPos, suppS.ePos, suppS.ePos - suppS.sPos, suppS.reason),
	    '<textarea rows="%d" cols="%d">' % (textareaHeight, textareaWidth),
	    suppS.text,
	    '</textarea>',
	'''
	<p>
	<b>Whole extracted text</b> <small>%d chars</small>
	<BR>
	''' % (lenText),
	    '<textarea rows="%d" cols="%d">' % (textareaHeight, textareaWidth),
	    refInfo['extractedtext'],
	    '</textarea>',
    ]
    return '\n'.join(body)
# ----------------------------

def getParameters():
    form = cgi.FieldStorage()

    params = {}
    for k in form.keys():
	params[k] = form.getvalue(k)
    return params
# ----------------------------

def buildPage(params):
    head = """Content-type: text/html

	<HTML><HEAD><TITLE>Extracted Text Section Splitting</TITLE>
	<STYLE>
	table, th, td { border: 1px solid black; }
	.header { border: thin solid black; vertical-align: top; font-weight: bold }
	.value { border: thin solid black; vertical-align: top; }.highlight { background-color: yellow; }
	.right { text-align: right; }
	</STYLE>
	</HEAD>
	<BODY>
	<H3>Predicted Sections</H3>
	"""
    paramReport = []
    if False:	# debugging
	paramReport = ['<p>Parameters']
	for i in params.items():
	    paramReport.append( '<br>%s: %s' % (i[0], i[1]) )
	paramReport.append('<br>End Parameters' )

    form = ['''
	    <DIV CLASS="search">
	    <FORM ACTION="splitter.cgi" METHOD="GET">
	    <B>PubMed ID </B>
	    <INPUT NAME="pubmed" TYPE="text" SIZE="25" autofocus>
	    OR <B>PDF filename </B>
	    <INPUT NAME="pdffile" TYPE="text" SIZE="25">
	    <INPUT TYPE="submit" VALUE="Go">
	    <small>/mgi/all/wts_projects/12700/12763/Data_splitter_test </small>
	    </FORM>
	    </DIV>
	    ''']
	    #'<INPUT NAME="isHidden" TYPE="hidden" VALUE="cannot see me">',

    refInfo = ''
    if params.has_key('pdffile'):
	refInfo = getPDFfile(params['pdffile'])
    elif params.has_key('pubmed'):
	refInfo = getReferenceInfo(params['pubmed'])

    if type(refInfo) == type(''):
	refDisplay = refInfo
    else:
	refDisplay = buildReferenceDetails(refInfo)

    #refDisplay = 'here is some stuff'
    body = '\n'.join(paramReport) + '\n'.join(form) + refDisplay

    tail = '</BODY></HTML>'
    print head + body + tail
    return
# ----------------------------

buildPage(getParameters())
