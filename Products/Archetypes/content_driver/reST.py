from docutils.core import publish_string
from ContentDriver import ContentDriver
from Products.Archetypes.debug import log
import sys
import sys
if sys.version_info < (2,2):
    # fix the types module to make it docutils working with py2.1
    import types
    types.StringTypes = (types.UnicodeType, types.StringType)

class Warnings:
    def __init__(self):
        self.messages = []

    def write(self, message):
        self.messages.append(message)

class Converter(ContentDriver):
  mime_type = 'text/restructured'

  def convertData(self, instance, data):
      # format with strings
      from html4zope import Writer
      settings_overrides = {'report_level': 1,
                            'halt_level': 6,
                            'warning_stream': Warnings()
                            }

      # do the format
      html = publish_string(writer=Writer(), source=data, settings_overrides=settings_overrides)

      # XXX what todo with this?
      #warnings = ''.join(pub.settings.warning_stream.messages)

      # do the format
      instance.html = html
      instance.text = data
