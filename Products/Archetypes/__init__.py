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
import os.path
try:
    __version__ = open(os.path.join(__path__[0], 'version.txt')).readline().strip()
except NameError:
    __version__ = 'unknown'

import Products.Archetypes.config
import Products.Archetypes.patches
import Products.Archetypes.registry


###
## security
###
from AccessControl import ModuleSecurityInfo
from AccessControl import allow_class
# make log and log_exc public
ModuleSecurityInfo('Products.Archetypes.lib.logging').declarePublic('log')
ModuleSecurityInfo('Products.Archetypes.lib.logging').declarePublic('log_exc')

# Plone compatibility in plain CMF. Templates should use IndexIterator from
# Archetypes and not from CMFPlone
try:
    from Products.CMFPlone.PloneUtilities import IndexIterator
except ImportError:
    from Products.Archetypes.lib.plonecompat import IndexIterator
allow_class(IndexIterator)

try:
    from Products.CMFPlone import transaction_note
except ImportError:
    from Products.Archetypes.lib.plonecompat import transaction_note
allow_class(transaction_note)

# make DisplayList accessible from python scripts and others objects executed
# in a restricted environment
from Products.Archetypes.lib.vocabulary import DisplayList
allow_class(DisplayList)

###
# register tools and content types
###
from Products.CMFCore.DirectoryView import registerDirectory
registerDirectory('skins', globals())

###
# Test dependencies
###
from Products.Archetypes.lib.utils import getPkgInfo
import Products.MimetypesRegistry
import Products.PortalTransforms
import Products.Marshall
mtr_info = getPkgInfo(Products.MimetypesRegistry)
pt_info = getPkgInfo(Products.PortalTransforms)

at_version = __version__
for info in (mtr_info, pt_info ):
    if not hasattr(info, 'at_versions'):
        raise RuntimeError('The product %s has no at_versions assigend. ' \
                           'Please update to a newer version.' % info.modname)
#    if at_version not in info.at_versions:
#        raise RuntimeError('The current Archetypes version %s is not in list ' \
#                           'of compatible versions for %s!\nList: %s' % \
#                           (at_version, info.modname, info.at_versions)
#                          )

from Products.Archetypes.lib.logging import log
try:
    import Products.generators
except ImportError:
    pass
else:
    log('Warning: Products.generator is deprecated, please remove the product')

try:
    import Products.validation
except ImportError:
    pass
else:
    log('Warning: Products.validation is deprecated, please remove the product')

###
# Tools
###
from Products.Archetypes.tool.archetypetool import ArchetypeTool
from Products.Archetypes.tool.ttwtool import ArchTTWTool

tools = (
    ArchetypeTool,
    ArchTTWTool,
    )

types_globals=globals()

def initialize(context):
    from Products.CMFCore import utils
    from Products.CMFCore import CMFCorePermissions

    from Products.Archetypes.atapi import process_types
    from Products.Archetypes.atapi import listTypes
    from Products.Archetypes.config import PKG_NAME
    from Products.Archetypes.config import REGISTER_DEMO_TYPES

    utils.ToolInit("%s Tool" % PKG_NAME, tools=tools,
                   product_name=PKG_NAME,
                   icon="tool.gif",
                   ).initialize(context)

    if REGISTER_DEMO_TYPES:
        import Products.Archetypes.example

        content_types, constructors, ftis = process_types(
            listTypes(PKG_NAME), PKG_NAME)

        utils.ContentInit(
            '%s Content' % PKG_NAME,
            content_types = content_types,
            permission = CMFCorePermissions.AddPortalContent,
            extra_constructors = constructors,
            fti = ftis,
            ).initialize(context)
    try:
        from Products.CMFCore.FSFile import FSFile
        from Products.CMFCore.DirectoryView import registerFileExtension
        registerFileExtension('xsl', FSFile)
        registerFileExtension('xul', FSFile)
    except ImportError:
        pass
