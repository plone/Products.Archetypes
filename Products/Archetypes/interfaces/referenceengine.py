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

from Interface import Interface, Attribute

class IReference(Interface):
    """ Reference """

    def UID():
        """the uid method for compat"""

    # Convenience methods
    def getSourceObject():
        """ returns the source end as object """

    def getTargetObject():
        """ returns the source end as object """

    # Catalog support
    def targetId():
        """ gives the id of the target object """

    def targetTitle():
        """ gives the title of the target object """


    # Policy hooks, subclass away
    def addHook(tool, sourceObject=None, targetObject=None):
        """gets called after reference object has been annotated to the object
        to reject the reference being added raise a ReferenceException """

    def delHook(tool, sourceObject=None, targetObject=None):
        """gets called before reference object gets deleted
        to reject the delete raise a ReferenceException """

    ###
    # OFS Operations Policy Hooks
    # These Hooks are experimental and subject to change
    def beforeTargetDeleteInformSource():
        """called before target object is deleted so
        the source can have a say"""

    def beforeSourceDeleteInformTarget():
        """called when the refering source Object is
        about to be deleted"""

    def _getURL():
        """the url used as the relative path based uid in the catalogs"""


class IContentReference(IReference):
    '''Subclass of Reference to support contentish objects inside references '''

    def getContentObject():
        """ gives the contentish object attached to the reference"""

class IReferenceCatalog(Interface):
    """Marker interface for reference catalog
    """

class IUIDCatalog(Interface):
    """Marker interface for uid catalog
    """
