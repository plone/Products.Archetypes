from ContentDriver import ContentDriver
import re

class Converter(ContentDriver):
  mime_type = "image/*"
  def convertData(self, instance, data):
    instance.html = self.makeImageRef()

  def makeImageRef(self):
      return '<img src="__IMG__">'

  def fixSubObjects(self, base, instance):
      html      = re.sub('__IMG__', base, instance.html)
      instance.html = html






