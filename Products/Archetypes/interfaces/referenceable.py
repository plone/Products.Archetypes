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

class IReferenceable(Interface):
    """ Referenceable """


    def getRefs(relationship=None):
        """get all the referenced objects for this object"""

    def getBRefs(relationship=None):
        """get all the back referenced objects for this object"""

    def getReferences(relationship=None):
        """ alias for getRefs """

    def getBackReferences(relationship=None):
        """ alias for getBRefs """

    def getReferenceImpl(relationship=None):
        """ returns the references as objects for this object """

    def getBackReferenceImpl(relationship=None):
        """ returns the back references as objects for this object """

    def UID():
        """ Unique ID """

    def reference_url():
        """like absoluteURL, but return a link to the object with this UID"""

    def hasRelationshipTo(target, relationship=None):
        """test is a relationship exists between objects"""

    def addReference(target, relationship=None, **kwargs):
        """add a reference to target. kwargs are metadata"""

    def deleteReference(target, relationship=None):
        """delete a ref to target"""

    def deleteReferences(relationship=None):
        """delete all references from this object"""

    def getRelationships():
        """list all the relationship types this object has refs for"""
