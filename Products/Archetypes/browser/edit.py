from zope.component import queryUtility
from zope.interface import implements

from Acquisition import aq_inner
from zExceptions import Unauthorized
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
        factory = getToolByName(aq_inner(self.context), 'portal_factory', None)
        if factory is not None:
            return factory.isTemporary(aq_inner(self.context))
        return False

    def isMultiPageSchema(self):
        return IMultiPageSchema.providedBy(self.context)

    def fieldsets(self):
        context = aq_inner(self.context)
        schematas = context.Schemata()
        return [
            key for key in schematas.keys()
            if (schematas[key].editableFields(context, visible_only=True))
            ]

    def fields(self, fieldsets):
        context = aq_inner(self.context)
        schematas = context.Schemata()
        return [f for key in fieldsets
                  for f in schematas[key].editableFields(context)]

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


# This is a helper to make sure the user gets a login form if they go to
# /edit on an unauthorized context.
class UnauthorizedEdit(BrowserView):
    
    def __call__(self):
        raise Unauthorized
