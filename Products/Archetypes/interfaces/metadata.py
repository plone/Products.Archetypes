from Products.CMFCore.interfaces.DublinCore import DublinCore, CatalogableDublinCore, MutableDublinCore

class IExtensibleMetadata(DublinCore, CatalogableDublinCore, MutableDublinCore):
    """ Archetypes implementation of DublinCore metadata """
    pass
