from Products.Archetypes.content_driver.ContentDriver import ContentDriver
from Products.Archetypes.debug import log, log_exc
import re, os, tempfile

class PDFDocument:

    def __init__(self, name, data):
        "Initialization : create tmp work directory and copy the document into a file."
        self.prefix = "/usr" # The path prefix where pdftotext is installed (usualy /usr or /usr/local)
        self.tmpdir = tempfile.mktemp()
        self.name = name
        self.data = data
        os.mkdir('%s' % self.tmpdir)
        filedest = open("%s/%s.pdf" % (self.tmpdir, self.name), "w")
        filedest.write(self.data)
        filedest.close()

    def Convert(self):
        "Convert the document"
        os.system('cd "%s" && %s/bin/pdftotext "%s.pdf" "%s.txt"' % (self.tmpdir, self.prefix, self.name, self.name))

    def cleandir(self):
        for f in os.listdir("%s" % self.tmpdir):
            os.remove("%s/%s" % (self.tmpdir, f))
        os.rmdir("%s" % self.tmpdir)

    def getHTML(self):
        return ''

    def getText(self):
        textfile_name = "%s/%s.txt" % (self.tmpdir, self.name)
        if os.path.exists(textfile_name):
            textfile = open(textfile_name, 'r')
            text = textfile.read()
            textfile.close()
            return text
        else:
            return ''

    # You wish :]
    # def getImages(self):
    #         imgs = []
    #         for f in os.listdir(self.tmpdir):
    #             result = re.match("^.+\.(?P<ext>.+)$", f)
    #             if result is not None:
    #                 ext = result.group('ext')
    #                 if ext in ('png', 'jpg', 'gif', 'wmz', 'wmf'): imgs.append(f)
    #         path = "%s/" % self.tmpdir
    #         return path, imgs

class Converter(ContentDriver):
    mime_type = 'application/pdf'


    def convertData(self, instance, data):
        doc = PDFDocument(instance.filename, data)
        doc.Convert()
        instance.html = doc.getHTML()
        instance.text = doc.getText()

        doc.cleandir()


