from ContentDriver import ContentDriver
from Products.Archetypes.debug import log, log_exc
from utils import bodyfinder, stylefinder
import re, os, tempfile

EXTRACT_BODY  = 1
EXTRACT_STYLE = 0

# XXX This is really a quick hack in more ways than one .. The converter
# used, rtf2html, is 14Kb of C code from 1993 with no canonical homepage
# AFAIK. 
#
# From its README:
#
# This version of rtf2html was developed by Dmitry Porapov
# <dpotapov@capitalsoft.com>, based on earlier work of Chuck Shotton.


class RTFDocument:

    def __init__(self, name, data):
        """ Initialization : create tmp work directory and copy the
            document into a file.
        """
        self.prefix = "/usr/local" # The path prefix where rtf2html is installed (usualy /usr or /usr/local)
        self.tmpdir = tempfile.mktemp()
        self.name = name
        self.data = data
        os.mkdir('%s' % self.tmpdir)
        filedest = open("%s/%s.rtf" % (self.tmpdir, self.name), "w")
        filedest.write(self.data)
        filedest.close()
    
    def Convert(self):
        "Convert the document"
        os.system('cd "%s" && %s/bin/rtf2html "%s.rtf" > "%s.html"' % (self.tmpdir, self.prefix, self.name, self.name))

    def cleandir(self):
        for f in os.listdir("%s" % self.tmpdir):
            os.remove("%s/%s" % (self.tmpdir, f))
        os.rmdir("%s" % self.tmpdir)
    
    def getHTML(self):
        htmlfile = open("%s/%s.html" % (self.tmpdir, self.name), 'r')
        html = htmlfile.read()
        htmlfile.close()
        return html


class Converter(ContentDriver):
    mime_type = 'application/rtf' 


    def convertData(self, instance, data):
        doc = RTFDocument(instance.filename, data)
        doc.Convert()
        instance.html = doc.getHTML()

        if EXTRACT_BODY:
            if EXTRACT_STYLE:
                style =  stylefinder(instance.html)
            else:
                style = '' 
            body  = bodyfinder(instance.html)

        instance.html = "%s\n%s" % (style, body)

        doc.cleandir()

