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

import os
import sys
from types import StringType, UnicodeType
import time
import urllib

from Products.Archetypes.lib.logging import log, log_exc
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.referenceengine import IReference
from Products.Archetypes.interfaces.referenceengine import IContentReference
from Products.Archetypes.interfaces.referenceengine import IReferenceCatalog
from Products.Archetypes.interfaces.referenceengine import IUIDCatalog
from Products.Archetypes.config import UID_CATALOG
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.config import UUID_ATTR
from Products.Archetypes.config import REFERENCE_ANNOTATION
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.config import STRING_TYPES
from Products.Archetypes.exceptions import ReferenceException
from Products.Archetypes.refengine.referenceable import Referenceable
from Products.Archetypes.lib.utils import unique
from Products.Archetypes.lib.utils import make_uuid
from Products.Archetypes.lib.utils import getRelURL
from Products.Archetypes.lib.utils import getRelPath
from Products.Archetypes.lib.utils import shasattr

from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from AccessControl import ClassSecurityInfo
from ExtensionClass import Base
from OFS.SimpleItem import SimpleItem
from OFS.ObjectManager import ObjectManager

from Globals import InitializeClass, DTMLFile
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.utils import UniqueObject
from Products.CMFCore import CMFCorePermissions
from Products.BTreeFolder2.BTreeFolder2 import BTreeFolder2
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from Products.ZCatalog.ZCatalog import ZCatalog
from Products.ZCatalog.Catalog import Catalog
from Products.ZCatalog.CatalogBrains import AbstractCatalogBrain
from Products import CMFCore
from ZODB.POSException import ConflictError
import zLOG

_www = os.path.join(os.path.dirname(__file__), 'www')
_catalog_dtml = os.path.join(os.path.dirname(CMFCore.__file__), 'dtml')


class Reference(Referenceable, SimpleItem):
    ## Added base level support for referencing References
    ## They respond to the UUID protocols, but are not
    ## catalog aware. This means that you can't move/rename
    ## reference objects and expect them to work, but you can't
    ## do this anyway. However they should fine the correct
    ## events when they are added/deleted, etc

    __implements__ = Referenceable.__implements__ + (IReference,)

    security = ClassSecurityInfo()
    portal_type = 'Reference'
    meta_type = 'Reference'

    # XXX FIXME more security

    manage_options = (
        (
        {'label':'View', 'action':'manage_view',
         },
        )+
        SimpleItem.manage_options
        )

    security.declareProtected(CMFCorePermissions.ManagePortal,
                              'manage_view')
    manage_view = PageTemplateFile('view_reference', _www)

    def __init__(self, id, sid, tid, relationship, **kwargs):
        self.id = id
        setattr(self, UUID_ATTR,  id)

        self.sourceUID = sid
        self.targetUID = tid
        self.relationship = relationship

        self.__dict__.update(kwargs)

    def __repr__(self):
        return "<Reference sid:%s tid:%s rel:%s>" %(self.sourceUID, self.targetUID, self.relationship)

    def UID(self):
        """the uid method for compat"""
        return getattr(aq_base(self), UUID_ATTR)

    ###
    # Convenience methods
    def getSourceObject(self):
        tool = getToolByName(self, UID_CATALOG)
        if not tool: return ''
        brains = tool(UID=self.sourceUID)
        for brain in brains:
            obj = brain.getObject()
            if obj is not None:
                return obj

    def getTargetObject(self):
        tool = getToolByName(self, UID_CATALOG, None)
        if not tool: return ''
        brains = tool(UID=self.targetUID)
        for brain in brains:
            obj = brain.getObject()
            if obj is not None:
                return obj

    ###
    # Catalog support
    def targetId(self):
        target = self.getTargetObject()
        if target is not None:
            return target.getId()
        return ''

    def targetTitle(self):
        target = self.getTargetObject()
        if target is not None:
            return target.Title()
        return ''

    def Type(self):
        return self.__class__.__name__

    ###
    # Policy hooks, subclass away
    def addHook(self, tool, sourceObject=None, targetObject=None):
        #to reject the reference being added raise a ReferenceException
        pass

    def delHook(self, tool, sourceObject=None, targetObject=None):
        #to reject the delete raise a ReferenceException
        pass

    ###
    # OFS Operations Policy Hooks
    # These Hooks are experimental and subject to change
    def beforeTargetDeleteInformSource(self):
        """called before target object is deleted so
        the source can have a say"""
        pass

    def beforeSourceDeleteInformTarget(self):
        """called when the refering source Object is
        about to be deleted"""
        pass

    def manage_afterAdd(self, item, container):
        Referenceable.manage_afterAdd(self, item, container)

        # when copying a full site containe is the container of the plone site
        # and item is the plone site (at least for objects in portal root)
        base = container
        try:
            rc = getToolByName(base, REFERENCE_CATALOG)
        except:
            base = item
            rc = getToolByName(base, REFERENCE_CATALOG)
        url = getRelURL(base, self.getPhysicalPath())
        rc.catalog_object(self, url)


    def manage_beforeDelete(self, item, container):
        Referenceable.manage_beforeDelete(self, item, container)
        rc  = getToolByName(container, REFERENCE_CATALOG)
        url = getRelURL(container, self.getPhysicalPath())
        rc.uncatalog_object(url)

InitializeClass(Reference)

REFERENCE_CONTENT_INSTANCE_NAME = 'content'

class ContentReference(ObjectManager, Reference):
    '''Subclass of Reference to support contentish objects inside references '''

    __implements__ = Reference.__implements__ + (IContentReference,)

    def __init__(self, *args, **kw):
        Reference.__init__(self, *args, **kw)


    security = ClassSecurityInfo()
    # XXX FIXME more security

    def addHook(self, *args, **kw):
        # creates the content instance
        if type(self.contentType) in (type(''),type(u'')):
            # type given as string
            tt=getToolByName(self,'portal_types')
            tt.constructContent(self.contentType, self,
                                REFERENCE_CONTENT_INSTANCE_NAME)
        else:
            # type given as class
            setattr(self, REFERENCE_CONTENT_INSTANCE_NAME,
                    self.contentType(REFERENCE_CONTENT_INSTANCE_NAME))
            getattr(self, REFERENCE_CONTENT_INSTANCE_NAME)._md=PersistentMapping()

    def delHook(self, *args, **kw):
        # remove the content instance
        if type(self.contentType) in (type(''),type(u'')):
            # type given as string
            self._delObject(REFERENCE_CONTENT_INSTANCE_NAME)
        else:
            # type given as class
            delattr(self, REFERENCE_CONTENT_INSTANCE_NAME)

    def getContentObject(self):
        return getattr(self.aq_inner.aq_explicit, REFERENCE_CONTENT_INSTANCE_NAME)

    def manage_afterAdd(self, item, container):
        Reference.manage_afterAdd(self, item, container)
        ObjectManager.manage_afterAdd(self, item, container)

    def manage_beforeDelete(self, item, container):
        ObjectManager.manage_beforeDelete(self, item, container)
        Reference.manage_beforeDelete(self, item, container)

InitializeClass(ContentReference)

class ContentReferenceCreator:
    '''Helper class to construct ContentReference instances based
       on a certain content type '''

    security = ClassSecurityInfo()

    def __init__(self,contentType):
        self.contentType=contentType

    def __call__(self,*args,**kw):
        #simulates the constructor call to the reference class in addReference
        res=ContentReference(*args,**kw)
        res.contentType=self.contentType

        return res

InitializeClass(ContentReferenceCreator)

class HoldingReference(Reference):
    def beforeTargetDeleteInformSource(self):
        raise ReferenceException, ("Can't delete target, "
                                   "its held by %s" %
                                   self.getSourceObject().absolute_url())

class CascadeReference(Reference):
    def beforeSourceDeleteInformTarget(self):
        tObj = self.getTargetObject()
        parent = tObj.aq_parent
        parent._delObject(tObj.id)


FOLDERISH_REFERENCE="at_folder_reference"
class FolderishReference(Reference):
    """Used by reference folder under the covers of the folderish API"""

    def __init__(self, id, sid, tid,
                 relationship=FOLDERISH_REFERENCE, **kwargs):
        Reference.__init__(self, id, sid, tid, relationship, **kwargs)

    def beforeSourceDeleteInformTarget(self):
        # The idea is that a reference folder would be
        # incrementing the reference count on its children
        # but not actually, placefully contain the object.
        # if the count is not 1 (meaning the last reference)
        # then we reject the delete
        if len(self.getTargetObject().getBRefs(FOLDERISH_REFERENCE)) != 1:
            raise ReferenceException, ("Can't delete target, "
                                       "its held by %s" %
                                       self.getSourceObject().absolute_url())
