from ContentDriver import ContentDriver
from Products.Archetypes.debug import log, log_exc #DBG 
import re, os, tempfile

class Converter(ContentDriver):
    mime_type = 'text/xml' 


    def convertData(self, instance, data):
        doc = DocBook(instance.filename, data)
        doc.Convert()
        instance.html = doc.getHTML()

        # instance.html = "%s\n%s" % (style, body)

        # path, images = doc.getImages()
        # self.importImages(instance, path, images)
        doc.cleandir()


    def _fixImage(self, matchObj):
        filename = matchObj.group('filename')
        fixed = basename(filename)
        text = matchObj.group(0)[:-len(filename)-1]
        text = '%s__IMG__/%s"' %(text, fixed)
        return text

    def fixSubObjects(self, base, instance):
        # imgRe = re.compile('<img.+?src="(?P<filename>[^"]+?)"', re.I | re.DOTALL)
        # html = imgRe.sub(self._fixImage, instance.html)
        # html = re.sub('__IMG__', base, html)
        # instance.html = html
        pass


    def importImages(self, instance, path, images):
        for imgname in images:
            try:
                modname = basename(imgname)
                if hasattr(instance, modname):
                    instance.manage_delObjects([modname])

                file = open(os.path.join(path, imgname), 'rb')
                data = file.read()
                file.close()
                instance.manage_addImage("%s" %(modname), data)
            except:
                log_exc()

        return 1


class DocBook:

    def __init__(self, name, data):
        """ Initialization: create tmp work directory and copy the document
            into a file.
        """
        self.prefix = "/usr" # The path prefix where xsltproc is installed
        self.tmpdir = tempfile.mktemp()
        log('DocBook.__init__> self.tmpdir: %s'%self.tmpdir) #DBG 
        self.name = name
        self.data = data
        os.mkdir('%s' % self.tmpdir)
        filedest = open("%s/%s.dbk" % (self.tmpdir, self.name), "w")
        filedest.write(self.data)
        filedest.close()
    
    def Convert(self):
        "Convert the document"
        command = 'cd "%s" && %s/bin/xsltproc %s/share/sgml/docbook/xsl-stylesheets-1.52.2/html/docbook.xsl "%s.dbk" > "%s.html"' % (self.tmpdir, self.prefix, self.prefix, self.name, self.name)
        log('Convert> %s'%command) #DBG 
        os.system(command)
        log('Convert> converted') #DBG 

    def cleandir(self):
        for f in os.listdir("%s" % self.tmpdir):
            os.remove("%s/%s" % (self.tmpdir, f))
        os.rmdir("%s" % self.tmpdir)
        
    def getHTML(self):
        log('getHTML> tmpdir: %s, name: %s'%(self.tmpdir, self.name)) #DBG 
        htmlfile = open("%s/%s.html" % (self.tmpdir, self.name), 'r')
        log('getHTML> about to read') #DBG 
        html = htmlfile.read()
        log('getHTML> read') #DBG 
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
        log('getImages> path: %s, imgs: %s'%(path, imgs)) #DBG 
        return path, imgs
