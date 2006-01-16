from ContentType import ContentType, addContentType, selectPlugin, \
registerConverter, getDefaultPlugin, lookupContentType, getConverter
from Products.Archetypes.debug import log, log_exc

import HTML
import ST
import Dumb
import Image
import PDF
import RTF
import DocBook


try:
    import MSWord
    registerConverter(MSWord.Converter(),
                      addContentType(ContentType("MSWord Document",
                                                 mime_types=['application/msword'],
                                                 extensions=['.doc'],
                                                 binary=1,
                                                 icon="topic_icon.gif",
                                                 )))
except:
    log_exc()
    log("""Unable to import MSWord content driver, this is most likely due to
    missing the win32 extensions on win32 for which COM is used to support
    document conversion. See the README.txt""")

try:
    import reST
    registerConverter(reST.Converter(),
                      addContentType(ContentType("reStructuredText",
                                                 mime_types=['text/restructured'],
                                                 extensions=['.restx']
                                                 )))
except:
    log_exc()
    log("""Unable to import reST content driver, this is most likely to do
    missing the docutils python package. Get a CVS checkout from http://docutils.sourceforge.net/""")


registerConverter(HTML.Converter(),
                  addContentType(ContentType("HTML Document",
                                             mime_types=['text/html'],
                                             extensions=['.html', '.htm']
                                             )))

registerConverter(Dumb.Converter(),
                  addContentType(ContentType("Plain Text",
                                             mime_types=['text/plain'],
                                             extensions=['.txt']
                                             ), default=1))

registerConverter(ST.Converter(),
                  addContentType(ContentType("Structured Text",
                                             mime_types=['text/structured'],
                                             extensions=['.stx']
                                             )))

registerConverter(Image.Converter(),
                  addContentType(ContentType("Image",
                                             mime_types=['image/*'],
                                             extensions=['.gif', '.png', '.jpg'],
                                             binary=1,
                                           )))

registerConverter(PDF.Converter(),
                  addContentType(ContentType("PDF Document",
                                             mime_types=['application/pdf',],
                                             binary=1,
                                             extensions=['.pdf',]
                                             )))

registerConverter(RTF.Converter(),
                  addContentType(ContentType("RTF Document",
                                             mime_types=['application/rtf',],
                                             binary=1,
                                             extensions=['.rtf',]
                                             )))

registerConverter(DocBook.Converter(),
                  addContentType(ContentType("DocBook Document",
                                             mime_types=['text/xml',],
                                             binary=1,
                                             extensions=['.dbk',]
                                             )))

## import Audio
## registerConverter(Audio.Converter(),
##                   addContentType(ContentType("Audio",
##                                              mime_types=['audio/*'],
##                                              extensions=['wav', 'au', 'mp3', 'ogg'],
##                                              binary=1,
##                                              )))
