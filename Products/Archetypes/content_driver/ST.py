from Products.CMFCore.utils import format_stx
from ContentDriver import ContentDriver
from Products.Archetypes.debug import log

class Converter(ContentDriver):
  mime_type = 'text/structured' 

  def convertData(self, instance, data):
    instance.html = format_stx(text=data, level=1)
    instance.text = data
