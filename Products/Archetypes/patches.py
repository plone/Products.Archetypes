"""
"""

# patch 1:
# Fixes #1013363 (renaming of folders nukes all references to AT objects inside
# them)

def manage_beforeDelete(self, item, container):
    self._at_orig_manage_beforeDelete(item, container)
    #and reset the rename flag (set in Referenceable._notifyCopyOfCopyTo)
    self._v_cp_refs = None

from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
CMFCatalogAware._at_orig_manage_beforeDelete = CMFCatalogAware.manage_beforeDelete
CMFCatalogAware.manage_beforeDelete = manage_beforeDelete

def _notifyOfCopyTo(self, container, op=0):
    self._at_orig_notifyOfCopyTo(container, op=op)
    # keep reference info internally when op == 1 (move)
    # because in those cases we need to keep refs
    if op==1: self._v_cp_refs = 1

from Products.CMFCore.PortalContent import PortalContent
PortalContent._at_orig_notifyOfCopyTo = PortalContent._notifyOfCopyTo
PortalContent._notifyOfCopyTo = _notifyOfCopyTo

try:
    from Products.CMFCore.PortalFolder import PortalFolderBase as PortalFolder
except:
    from Products.CMFCore.PortalFolder import PortalFolder

PortalFolder._at_orig_notifyOfCopyTo = PortalFolder._notifyOfCopyTo
PortalFolder._notifyOfCopyTo = _notifyOfCopyTo
