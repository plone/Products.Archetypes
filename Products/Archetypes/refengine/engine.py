"""ReferenceEngine module alias helper

This module contains classes that where formally known as
Products.Archetypes.ReferenceEngine.CLASS. It's used by patches.py to create an
alias.
"""
from Products.Archetypes.refengine.pluggablecatalog import PluggableCatalog

from Products.Archetypes.refengine.referencecatalog import ReferenceCatalogBrains
from Products.Archetypes.refengine.referencecatalog import ReferenceBaseCatalog
from Products.Archetypes.refengine.referencecatalog import ReferenceResolver
from Products.Archetypes.refengine.referencecatalog import ReferenceCatalog

from Products.Archetypes.refengine.references import Reference
from Products.Archetypes.refengine.references import ContentReference
from Products.Archetypes.refengine.references import ContentReferenceCreator

from Products.Archetypes.refengine.uidcatalog import UIDCatalogBrains
from Products.Archetypes.refengine.uidcatalog import UIDBaseCatalog
from Products.Archetypes.refengine.uidcatalog import UIDCatalog
