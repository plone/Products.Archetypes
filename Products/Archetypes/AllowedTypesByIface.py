###############################################################################
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
# * Neither the name of the author nor the names of its contributors may be
#   used to endorse or promote products derived from this software without
#   specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
###############################################################################

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.atapi import BaseFolder
from Products.Archetypes.ArchetypeTool import listTypes

class AllowedTypesByIfaceMixin:
    """An approach to restrict allowed content types in a container by
    the interfaces they implement.

    Notice that extending this class means surpassing allowed_content_types,
    filter_content_types etc in the FTI, while we are still concerned about
    security.

    ATBIFolder is an example type that uses AllowedTypesByIfaceMixin:

    >>> self.folder.invokeFactory('ATBIFolder', 'f')
    'f'

    >>> f = self.folder.f

    f has an empty list of allowed_interfaces, so it doesn't allow anything
    right now:

    >>> f.allowedContentTypes()
    []

    invokeFactory will fail:

    >>> try:
    ...     f.invokeFactory('SimpleType', 'st')
    ... except ValueError:
    ...     print 'Right'
    Right

    Now we restrict allowed_interfaces to IBaseFolder:

    >>> from Products.Archetypes.interfaces.base import *
    >>> f.allowed_interfaces = (IBaseFolder,)

    And try to add a SimpleType, which fails again:

    >>> try:
    ...     f.invokeFactory('SimpleType', 'st')
    ... except ValueError:
    ...     print 'Right'
    Right

    SimpleFolder implements IBaseFolder:

    >>> f.invokeFactory('SimpleFolder', 'sf')
    'sf'

    A content object only needs to implement one of allowed_interfaces:

    >>> from zope.interface import Interface
    >>> class SomeInterface(Interface): pass
    >>> f.allowed_interfaces = (IBaseFolder, SomeInterface)
    >>> f.invokeFactory('SimpleFolder', 'sf2')
    'sf2'
    >>> try:
    ...     f.invokeFactory('SimpleType', 'sf')
    ... except ValueError:
    ...     print 'Right'
    Right

    """

    # XXX: This class depends heavily on implementation details in CMF's
    #      PortalFolder.

    allowed_interfaces = () # Don't allow anything, subclasses overwrite!

    def allowedContentTypes(self):
        """Redefines CMF PortalFolder's allowedContentTypes."""
        at = getToolByName(self, 'archetype_tool')
        return at.listPortalTypesWithInterfaces(self.allowed_interfaces)

    def invokeFactory(self, type_name, id, RESPONSE = None, *args, **kwargs):
        """Invokes the portal_types tool.

        Overrides PortalFolder.invokeFactory."""
        pt = getToolByName(self, 'portal_types')
        at = getToolByName(self, 'archetype_tool')
        fti = None
        for t in listTypes():
            if t['portal_type'] == type_name:
                fti = t
                break

        if fti is None:
            raise ValueError, "Type %r not available." % type_name

        if not at.typeImplementsInterfaces(fti, self.allowed_interfaces):
            raise ValueError, "Type %r does not implement any of %s." % \
                  (type_name, self.allowed_interfaces)

        args = (type_name, self, id, RESPONSE) + args
        new_id = pt.constructContent(*args, **kwargs)
        if not new_id: new_id = id
        return new_id

    def _verifyObjectPaste(self, object, validate_src=1):
        """Overrides PortalFolder._verifyObjectPaste."""
        # XXX: What we do here is trick
        #      PortalFolder._verifyObjectPaste in its check for
        #      allowed content types. We make our typeinfo temporarily
        #      unavailable.
        pt = getToolByName(self, 'portal_types')
        tmp_name = '%s_TMP' % self.portal_type
        ti = pt.getTypeInfo(self.portal_type)
        pt.manage_delObjects([self.portal_type])
        try:
            value = BaseFolder._verifyObjectPaste(self, object, validate_src)
        finally:
            pt._setObject(self.portal_type, ti)
        return value
