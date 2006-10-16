from zope.interface import implements
from zope.component import getMultiAdapter

from Products.Five import BrowserView

from Products.Archetypes.interfaces import IEdit
from Products.Archetypes.interfaces import IMultiPageSchema

class Edit(BrowserView):
    implements(IEdit)

    def isMultiPageSchema(self):
        return IMultiPageSchema.providedBy(self.context)
