from zope.component import queryUtility
from zope.interface import implements

from Acquisition import aq_inner
from Products.Five import BrowserView

from Products.Archetypes.interfaces import IEditForm
from Products.Archetypes.interfaces import IMultiPageSchema

from Products.Archetypes import PloneMessageFactory as _

try:
    from Products.CMFPlone.interfaces import IFactoryTool
    HAVE_PORTAL_FACTORY = True
except ImportError:
    HAVE_PORTAL_FACTORY = False

class Edit(BrowserView):
    implements(IEditForm)

    def isTemporaryObject(self):
        if HAVE_PORTAL_FACTORY:
            factory = queryUtility(IFactoryTool)
            if factory is not None:
                return factory.isTemporary(aq_inner(self.context))
        return False

    def isMultiPageSchema(self):
        return IMultiPageSchema.providedBy(self.context)

    def getTranslatedSchemaLabel(self, schema):
        label = u"label_schema_%s" % schema
        default = unicode(schema).capitalize()
        return _(label, default=default)
