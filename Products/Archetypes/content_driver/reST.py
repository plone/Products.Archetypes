import docutils.core
from docutils.io import StringOutput, StringInput 
from ContentDriver import ContentDriver
from Products.Archetypes.debug import log
import sys

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
      pub = docutils.core.Publisher(writer=Writer())
      pub.set_reader('standalone', None, 'restructuredtext')
      
      # go with the defaults
      pub.get_settings()
      
      # this is needed, but doesn't seem to do anything
      pub.settings._destination = ''
      
      # use the stylesheet chosen by the user
      # XXX What is this?
      #pub.settings.stylesheet = 'plone.css'
      
      # set the reporting level to something sane
      pub.settings.report_level = 1
      
      # don't break if we get errors
      pub.settings.halt_level = 6

      # remember warnings
      pub.settings.warning_stream = Warnings()
      
      # input
      pub.source = StringInput(source=data,
                               encoding=sys.getdefaultencoding())

      # output - not that it's needed
      pub.destination = StringOutput(encoding=sys.getdefaultencoding())
      
      # parse!
      document = pub.reader.read(pub.source, pub.parser, pub.settings)

      # XXX what todo with this?
      #warnings = ''.join(pub.settings.warning_stream.messages) 
      
      # do the format
      instance.html = pub.writer.write(document, pub.destination)
      instance.text = data
