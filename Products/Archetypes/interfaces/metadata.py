from Interface import Interface, Attribute
from Products.CMFCore.interfaces.DublinCore import DublinCore
from Products.CMFCore.interfaces.DublinCore import CatalogableDublinCore
from Products.CMFCore.interfaces.DublinCore import MutableDublinCore

class IExtensibleMetadata(DublinCore, CatalogableDublinCore, MutableDublinCore):
    """ Archetypes implementation of DublinCore metadata """
    pass
