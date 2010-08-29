from Acquisition import aq_base

from zope.interface import implementer
from zope.component import adapter

from plone.uuid.interfaces import IUUID

from Products.Archetypes.config import UUID_ATTR
from Products.Archetypes.interfaces import IReferenceable

@implementer(IUUID)
@adapter(IReferenceable)
def referenceableUUID(context):
    return getattr(aq_base(context), UUID_ATTR, None)
