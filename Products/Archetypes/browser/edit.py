from zope.interface import implements
from zope.component import getMultiAdapter

from Products.Five import BrowserView

from Products.Archetypes.interfaces import IEdit
from Products.Archetypes.interfaces import IMultiPageSchema

from Products.Archetypes import PloneMessageFactory as _

class Edit(BrowserView):
    implements(IEdit)

    def isMultiPageSchema(self):
        return IMultiPageSchema.providedBy(self.context)

    def getTranslatedSchemaLabel(self, schema):
        label = u"label_schema_%s" % schema
        default = unicode(schema).capitalize()
        return _(label, default=default)
