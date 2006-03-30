# BBB
try:
    from Products.CMFCore.interfaces import CatalogableDublinCore
except ImportError:
    from Products.CMFCore.interfaces.DublinCore import DublinCore, CatalogableDublinCore, MutableDublinCore
    import Products.CMFCore.interfaces as module
    from Products.Archetypes import utils
    utils.makeZ2Bridges(module, DublinCore, CatalogableDublinCore, MutableDublinCore)

from Products.CMFCore.interfaces import DublinCore, CatalogableDublinCore, MutableDublinCore

class IExtensibleMetadata(DublinCore, CatalogableDublinCore, MutableDublinCore):
    """ Archetypes implementation of DublinCore metadata """
    pass
