from ContentDriver import ContentDriver

class Converter(ContentDriver):
  mime_type = "text/html"
  def convertData(self, instance, data):
    instance.html = data



