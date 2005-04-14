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

from Products.Archetypes.config import INSTALL_DEMO_TYPES
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.atapi import listTypes
from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes.Extensions.utils import setupEnvironment
from Products.Archetypes.Extensions.utils import setupArchetypes
from StringIO import StringIO

def install(self, include_demo=None, require_dependencies=1):
    out=StringIO()

    if not hasattr(self, "_isPortalRoot"):
        print >> out, "Must be installed in a CMF Site (read Plone)"
        return

    setupArchetypes(self, out, require_dependencies=require_dependencies)

    if include_demo or INSTALL_DEMO_TYPES:
        print >> out, "Installing %s" % listTypes(PKG_NAME)
        installTypes(self, out, listTypes(PKG_NAME), PKG_NAME,
                     require_dependencies=require_dependencies,
                     install_deps=0)
        print >> out, 'Successfully installed the demo types.'

    print >> out, 'Successfully installed %s' % PKG_NAME

    return out.getvalue()

def uninstall(portal):
    prod = getattr(portal.portal_quickinstaller, PKG_NAME)
    prod.portalobjects = [po for po in prod.portalobjects
                          if po[-8:] != '_catalog']
