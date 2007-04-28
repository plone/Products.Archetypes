from zope.interface import implements

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView

from Products.Archetypes.interfaces import IEditForm
from Products.Archetypes.interfaces import IMultiPageSchema

from Products.Archetypes import PloneMessageFactory as _

class Edit(BrowserView):
    implements(IEditForm)

    def isTemporaryObject(self):
        factory = getToolByName(aq_inner(self.context), 'portal_factory',
                                None)
        if factory is not None:
            return factory.isTemporary(aq_inner(self.context))
        else:
            return False

    def isMultiPageSchema(self):
        return IMultiPageSchema.providedBy(self.context)

    def getTranslatedSchemaLabel(self, schema):
        label = u"label_schema_%s" % schema
        default = unicode(schema).capitalize()
        return _(label, default=default)
