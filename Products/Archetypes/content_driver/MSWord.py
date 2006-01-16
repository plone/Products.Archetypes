from ContentDriver import ContentDriver
from Products.Archetypes.debug import log, log_exc
from utils import bodyfinder, stylefinder, stripMSTags, basename
import OFS.Image
import os.path
import re

EXTRACT_BODY  = 1
EXTRACT_STYLE = 0

FIX_IMAGES    = 1
IMAGE_PREFIX  = "img_"

import os
if os.name == 'posix':
    try:
        import PyUNO
        from OfficeDocumentUNO import OfficeDocument
    except:
        log("""Failed to import the OpenOffice PyUNO content converter.
        Remind me to write a doc on how to set this up as its a better
        converter than wvWare and in somecases even MSWord""")
        from OfficeDocument import OfficeDocument
else:
    from OfficeDocumentCOM import OfficeDocument



class Converter(ContentDriver):
    mime_type = 'application/msword'


    def convertData(self, instance, data):
        doc = OfficeDocument(instance.filename, data)
        doc.Convert()
        instance.html = doc.getHTML()

        if EXTRACT_BODY:
            if EXTRACT_STYLE:
                style =  stylefinder(instance.html)
            else:
                style = ''
            body  = bodyfinder(instance.html)
            body  = stripMSTags(body)

        instance.html = "%s\n%s" % (style, body)

        path, images = doc.getImages()
        self.importImages(instance, path, images)
        doc.cleandir()


    def _fixImage(self, matchObj):
        filename = matchObj.group('filename')
        fixed = basename(filename)
        text = matchObj.group(0)[:-len(filename)-1]
        text = '%s__IMG__/%s"' %(text, fixed)
        return text

    def fixSubObjects(self, base, instance):
        imgRe = re.compile('<img.+?src="(?P<filename>[^"]+?)"', re.I | re.DOTALL)
        html = imgRe.sub(self._fixImage, instance.html)
        html = re.sub('__IMG__', base, html)
        instance.html = html


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


