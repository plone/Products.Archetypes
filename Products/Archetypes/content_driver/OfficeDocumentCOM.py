import win32com, sys, string, win32api, traceback, re, tempfile, os
import win32com.client
from win32com.test.util import CheckClean
import pythoncom
from win32com.client import gencache
from win32com.client import constants, Dispatch
from pywintypes import Unicode
import os.path

# Warning:
# If you get a message saying the constant wdBrowserLevel cannot
# be found this means you need to run makepy see
# win32com/client/makepy.py for more information

class OfficeDocument:
    def __init__(self, name, data):
        "Initialization : create tmp work directory and copy the document into a file."
        self.name = name
        self.data = data
        self.tmpdir = tempfile.mktemp()
        os.mkdir(self.tmpdir)
        if not self.name.endswith('.doc'):
            name = self.name + ".doc"
        self.filedest = open("%s" % os.path.join(self.tmpdir, name), "wb")
        self.file     = self.filedest.name
        self.filedest.write(data)
        self.filedest.close()


    def Convert(self):
        pythoncom.CoInitialize()

        try:
            word = Dispatch("Word.Application")
            word.Visible = 0
            doc = word.Documents.Open(self.file)
            #Let's set up some html saving options for this document
            word.ActiveDocument.WebOptions.RelyOnCSS = 1
            word.ActiveDocument.WebOptions.OptimizeForBrowser = 1
            word.ActiveDocument.WebOptions.BrowserLevel = constants.wdBrowserLevelV4
            word.ActiveDocument.WebOptions.OrganizeInFolder = 0
            word.ActiveDocument.WebOptions.UseLongFileNames = 1
            word.ActiveDocument.WebOptions.RelyOnVML = 0
            word.ActiveDocument.WebOptions.AllowPNG = 1
            #And then save the document into HTML
            doc.SaveAs(FileName = "%s.htm" % (self.file), FileFormat = constants.wdFormatHTML)
            #TODO -- Extract Metadata (author, title, keywords) so we can populate the dublin core
            #Converter will need to be extended to return a dict of possible MD fields
            doc.Close()
            word.Quit()
        finally:
            win32api.Sleep(1000) #Waiting for Word to close
            pythoncom.CoUninitialize()

## This function has to be done. It's more difficult to delete the temp
## directory under Windows, because there is sometimes a directory in it.
    def cleandir(self):
        for f in os.listdir(self.tmpdir):
            os.remove("%s" % os.path.join(self.tmpdir, f))
        os.rmdir(self.tmpdir)

    def getHTML(self):
        htmlfile = open("%s.htm" % os.path.join(self.tmpdir, self.name), 'r')
        html = htmlfile.read()
        htmlfile.close()
        return html

    def getImages(self):
        imgs = []
        for f in os.listdir(self.tmpdir):
            result = re.match("^.+\.(?P<ext>.+)$", f)
            if result is None: continue
            ext = result.group('ext')
            if ext in ('png', 'jpg', 'gif', 'wmf', 'wmz'): imgs.append(f)

        path = "%s\\" % self.tmpdir
        return path, imgs

