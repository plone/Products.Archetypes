# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################
"""
"""

##############################################################################
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

from Products.CMFCore.PortalFolder import PortalFolder
PortalFolder._at_orig_notifyOfCopyTo = PortalFolder._notifyOfCopyTo
PortalFolder._notifyOfCopyTo = _notifyOfCopyTo

##############################################################################
# patch 2:
# module aliases for persistence
import sys

# import list of modules
from Products.Archetypes.tools import archetypetool
from Products.Archetypes.tools import ttwtool
from Products.Archetypes.refengine import engine
from Products.Archetypes.refengine import references
from Products.Archetypes.lib import baseunit
from Products.Archetypes.examples import complextype
from Products.Archetypes.examples import dynamicdocument
from Products.Archetypes.examples import fact
from Products.Archetypes.examples import refnode
from Products.Archetypes.examples import simplebtreefolder
from Products.Archetypes.examples import simplefile
from Products.Archetypes.examples import simplefolder
from Products.Archetypes.examples import simpletype

# alias mapping
mapping = {
    'Products.Archetypes.ArchetypeTool'   : archetypetool,
    'Products.Archetypes.ArchTTWTool'     : ttwtool,
    'Products.Archetypes.ReferenceEngine' : engine,
    'Products.Archetypes.references'      : references,
    'Products.Archetypes.BaseUnit'        : baseunit,
    'Products.Archetypes.examples.ComplexType'  : complextype,
    'Products.Archetypes.examples.DDocument'    : dynamicdocument,
    'Products.Archetypes.examples.Fact'         : fact,
    'Products.Archetypes.examples.RefNode'      : refnode,
    'Products.Archetypes.examples.SimpleBTreeFolder' : simplebtreefolder,
    'Products.Archetypes.examples.SimpleFile'   : simplefile,
    'Products.Archetypes.examples.SimpleFolder' : simplefolder,
    'Products.Archetypes.examples.SimpleType'   : simpletype,
    }

# create aliases from dottedpath to module
for dottedpath, module in mapping.items():
    sys.modules[dottedpath] = module
