from zope.component import queryUtility
from zope.interface import implements

from Acquisition import aq_inner
from Products.CMFCore.utils import getToolByName
from Products.Five import BrowserView

from Products.Archetypes.interfaces import IEditForm
from Products.Archetypes.interfaces import IMultiPageSchema

from Products.Archetypes import PloneMessageFactory as _

# Import conditionally, so we don't introduce a hard depdendency
try:
    from plone.i18n.normalizer.interfaces import IIDNormalizer
    ID_NORMALIZER = True
except ImportError:
    ID_NORMALIZER = False


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

    def normalizeString(self, text):
        if ID_NORMALIZER:
            norm = queryUtility(IIDNormalizer)
            if norm is not None:
                return norm.normalize(text)
        return text
