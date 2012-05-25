from Products.CMFCore.interfaces import ICatalogableDublinCore
from Products.CMFCore.interfaces import IMutableDublinCore


class IExtensibleMetadata(ICatalogableDublinCore, IMutableDublinCore):
    """ Archetypes implementation of DublinCore metadata """
