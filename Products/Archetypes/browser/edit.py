from zope.interface import implements
from zope.component import getMultiAdapter

from Products.Five import BrowserView as BaseView

from Products.Archetypes.interfaces import IEdit
from Products.Archetypes.interfaces import IMultiPageSchema

class BrowserView(BaseView):

    def __init__(self, context, request):
        self.context = [context]
        self.request = request

class Edit(BrowserView):
    implements(IEdit)

    def isMultiPageSchema(self):
        return IMultiPageSchema.providedBy(self.context)
