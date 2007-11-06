"""
Backward compatibility module.
"""
import sys
import generator
import ReferenceEngine
import UIDCatalog

# prevent failure of Products.generator module
sys.modules['Products.generator'] = generator

# don't break existing ZODB instances of UID catalog
ReferenceEngine.UIDBaseCatalog = UIDCatalog.UIDBaseCatalog
ReferenceEngine.UIDCatalog = UIDCatalog.UIDCatalog
