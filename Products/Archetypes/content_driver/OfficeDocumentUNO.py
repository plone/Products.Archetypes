from Products.Archetypes.debug import log, log_exc
import re, os, tempfile
from UNO import UNO


class OfficeDocument:
   def __init__(self, name, data):
       "Initialization : create tmp work directory and copy the document into a file."
       self.tmpdir = tempfile.mktemp()
       self.name = name
       self.data = data
       os.mkdir('%s' % self.tmpdir)
       if not name.endswith('.doc'):
           self.name = name + ".doc"
           
       filedest = open("%s/%s" % (self.tmpdir, self.name), "w")
       filedest.write(self.data)
       self.file = filedest.name
       filedest.close()
   
   def Convert(self):
       "Convert the document"
       xStorable = None
       try:
           rUNO = UNO()
           properties =  [ {
               'Name'  : 'Hidden',
               'Value' : rUNO.newBoolean(1)
               }
                           ]
           
           rProperties = rUNO.newPropertyValues ( properties )
           xStorable = rUNO.new ("file://%s" % self.file, propertyValues=rProperties )[0]
           
           properties = [ { 'Name' : 'FilterName',
                            'Value' : 'swriter: HTML (StarWriter)' },
                          { 'Name' : 'Overwrite',
                            'Value' : rUNO.newBoolean(1) }
                          ]
           
           rProperties = rUNO.newPropertyValues ( properties )
           
           xStorable.storeAsURL ("file://%s.html" % self.file, rProperties )
       except:
           log_exc()
           pass

           if xStorable is not None:
               xStorable.dispose()
               

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
