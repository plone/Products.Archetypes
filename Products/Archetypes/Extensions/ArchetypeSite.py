# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and 
#	                       the respective authors. All rights reserved.
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

try:
    from Products.CMFPlone.Portal import addPolicy
except ImportError:
    def addPolicy(name, cls):
        pass
    class DefaultCustomizationPolicy:
        pass
else:
    from Products.Archetypes.Extensions.Install import install as installArchetypes

class ArchetypeCustomizationPolicy(DefaultCustomizationPolicy):
    """ Install Plone with the Archetypes Package """

    def customize(self, portal):
        # do the base Default install, that gets
        # most of it right
        DefaultCustomizationPolicy.customize(self, portal)

        outStr = doCustomization(portal)
        return outStr.getvalue()

def doCustomization(self):
    from StringIO import StringIO
    out = StringIO()

    # Always include demo types
    result = installArchetypes(self, include_demo=1)
    print >> out, result

    return out.getvalue()

def register(context, app_state):
    addPolicy('Archetypes Site', ArchetypeCustomizationPolicy())

