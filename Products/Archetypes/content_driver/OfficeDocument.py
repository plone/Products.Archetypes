import re, os, tempfile
from utils import bin_search

class OfficeDocument:

    def __init__(self, name, data):
        "Initialization : create tmp work directory and copy the document into a file."
        self.tmpdir = tempfile.mktemp()
        self.name = name
        self.data = data
        os.mkdir('%s' % self.tmpdir)
        filedest = open("%s/%s.doc" % (self.tmpdir, self.name), "w")
        filedest.write(self.data)
        filedest.close()
        self.binary = bin_search("wvWare")
        
    def Convert(self):
        "Convert the document"
        os.system('cd "%s" && %s "%s.doc" > "%s.html"' % (self.tmpdir, self.binary, self.name, self.name))

    def cleandir(self):
        for f in os.listdir("%s" % self.tmpdir):
            os.remove("%s/%s" % (self.tmpdir, f))
        os.rmdir("%s" % self.tmpdir)
        
    def getHTML(self):
        htmlfile = open("%s/%s.html" % (self.tmpdir, self.name), 'r')
        html = htmlfile.read()
        htmlfile.close()
        return html

    def getImages(self):
        imgs = []
        for f in os.listdir(self.tmpdir):
            result = re.match("^.+\.(?P<ext>.+)$", f)
            if result is not None:
                ext = result.group('ext') 
                if ext in ('png', 'jpg', 'gif', 'wmz', 'wmf'): imgs.append(f)
        path = "%s/" % self.tmpdir
        return path, imgs
