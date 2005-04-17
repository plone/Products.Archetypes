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

from __future__ import nested_scopes

import os.path
import sys
from copy import deepcopy
from DateTime import DateTime
from StringIO import StringIO

from Products.Archetypes.interfaces.base import IBaseObject
from Products.Archetypes.interfaces.referenceable import IReferenceable
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata
from Products.Archetypes.interfaces.templatemixin import ITemplateMixin
from Products.Archetypes.lib.classgen import generateClass
from Products.Archetypes.lib.classgen import generateCtor
from Products.Archetypes.lib.classgen import generateZMICtor
from Products.Archetypes.storage.sql.config import SQLStorageConfig
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.config import UID_CATALOG
from Products.Archetypes.config import HAS_GRAPHVIZ
from Products.Archetypes.lib.logging import log
from Products.Archetypes.lib.utils import findDict
from Products.Archetypes.lib.vocabulary import DisplayList
from Products.Archetypes.lib.utils import mapply
from Products.Archetypes.render import renderService
from Products.Archetypes.registry import registerComponent
from Products.Archetypes.registry import getRegistry
from Products.Archetypes.lib.utils import getDottedName

from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.ActionProviderBase import ActionProviderBase
from Products.CMFCore.TypesTool import FactoryTypeInformation
from Products.CMFCore.utils import UniqueObject, getToolByName
from Products.CMFCore.interfaces.portal_catalog \
     import portal_catalog as ICatalogTool
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression

from AccessControl import ClassSecurityInfo
from Acquisition import ImplicitAcquisitionWrapper
from Globals import InitializeClass
from Globals import PersistentMapping
from OFS.Folder import Folder
from Products.ZCatalog.IZCatalog import IZCatalog
from Products.PageTemplates.PageTemplateFile import PageTemplateFile
from ZODB.POSException import ConflictError

try:
    from Products.CMFPlone.Configuration import getCMFVersion
except ImportError:
    # Configuration and getCMFVersion come with Plone 2.0
    def getCMFVersion():
        from os.path import join
        from Globals import package_home
        from Products.CMFCore import cmfcore_globals
        path = join(package_home(cmfcore_globals), 'version.txt')
        file = open(path, 'r')
        _version = file.read()
        file.close()
        return _version.strip()


# This is the template that we produce our custom types from
# Never actually used
base_factory_type_information = (
    { 'id': 'Archetype'
      , 'content_icon': 'document_icon.gif'
      , 'meta_type': 'Archetype'
      , 'description': ('Archetype for flexible types')
      , 'product': 'Unknown Package'
      , 'factory': 'addContent'
      , 'immediate_view': 'base_edit'
      , 'global_allow': True
      , 'filter_content_types': False
      , 'allow_discussion': False
      , 'actions': (
                     { 'id': 'view',
                       'name': 'View',
                       'action': 'string:${object_url}/base_view',
                       'permissions': (CMFCorePermissions.View,),
                       },

                     { 'id': 'edit',
                       'name': 'Edit',
                       'action': 'string:${object_url}/base_edit',
                       'permissions': (CMFCorePermissions.ModifyPortalContent,),
                       },

                     { 'id': 'metadata',
                       'name': 'Properties',
                       'action': 'string:${object_url}/base_metadata',
                       'permissions': (CMFCorePermissions.ModifyPortalContent,),
                       },

                     { 'id': 'references',
                       'name': 'References',
                       'action': 'string:${object_url}/reference_graph',
                       'condition': 'object/archetype_tool/has_graphviz',
                       'permissions': (CMFCorePermissions.ModifyPortalContent,
                                       CMFCorePermissions.ReviewPortalContent,),
                       'visible' : True,
                       },

                     { 'id': 'folderlisting',
                       'name': 'Folder Listing',
                       'action': 'string:${folder_url}/folder_listing',
                       'condition': 'object/isPrincipiaFolderish',
                       'permissions': (CMFCorePermissions.View,),
                       'category': 'folder',
                       'visible' : False,
                       },
                     )
      }, )

def fixActionsForType(portal_type, typesTool):
    if 'actions' in portal_type.installMode:
        typeInfo = getattr(typesTool, portal_type.portal_type)
        if hasattr(portal_type, 'actions'):
            # Look for each action we define in portal_type.actions in
            # typeInfo.action replacing it if its there and just
            # adding it if not
            if getattr(portal_type,'include_default_actions', True):
                new = list(typeInfo._actions)
            else:
                # If no standard actions are wished don't display them
                new = []

            cmfver = getCMFVersion()

            for action in portal_type.actions:
                # DM: "Expression" derives from "Persistent" and
                # we must not put persistent objects into class attributes.
                # Thus, copy "action"
                action = action.copy()

                if cmfver[:7] >= 'CMF-1.4' or cmfver == 'Unreleased':
                    # Then we know actions are defined new style as
                    # ActionInformations
                    hits = [a for a in new if a.id == action['id']]

                    # Change action and condition into expressions, if
                    # they are still strings
                    if action.has_key('action') and \
                      isinstance(action['action'], basestring):
                        action['action'] = Expression(action['action'])
                    if action.has_key('condition') and \
                           isinstance(action['condition'], basestring):
                        action['condition'] = Expression(action['condition'])
                    if hits:
                        hits[0].__dict__.update(action)
                    else:
                        if action.has_key('name'):
                            action['title'] = action['name']
                            del action['name']

                        new.append(ActionInformation(**action))
                else:
                    hit = findDict(new, 'id', action['id'])
                    if hit:
                        hit.update(action)
                    else:
                        new.append(action)

            # Update Aliases
            if cmfver[:7] >= 'CMF-1.4' or cmfver == 'Unreleased':
                if (hasattr(portal_type, 'aliases') and
                    hasattr(typeInfo, 'setMethodAliases')):
                    typeInfo.setMethodAliases(portal_type.aliases)
                else:
                    # Custom views might need to reguess the aliases
                    if hasattr(typeInfo, '_guessMethodAliases'):
                        typeInfo._guessMethodAliases()

            typeInfo._actions = tuple(new)
            typeInfo._p_changed = True

        if hasattr(portal_type, 'factory_type_information'):
            typeInfo.__dict__.update(portal_type.factory_type_information)
            typeInfo._p_changed = True


def modify_fti(fti, klass, pkg_name):
    fti[0]['id'] = klass.__name__
    fti[0]['meta_type'] = klass.meta_type
    fti[0]['description'] = klass.__doc__
    fti[0]['factory'] = 'add%s' % klass.__name__
    fti[0]['product'] = pkg_name

    if hasattr(klass, 'content_icon'):
        fti[0]['content_icon'] = klass.content_icon

    if hasattr(klass, 'global_allow'):
        fti[0]['global_allow'] = klass.global_allow

    if hasattr(klass, 'allow_discussion'):
        fti[0]['allow_discussion'] = klass.allow_discussion

    if hasattr(klass, 'allowed_content_types'):
        allowed = klass.allowed_content_types
        fti[0]['allowed_content_types'] = allowed
        fti[0]['filter_content_types'] = allowed and True or False

    if hasattr(klass, 'filter_content_types'):
        fti[0]['filter_content_types'] = klass.filter_content_types

    if hasattr(klass, 'immediate_view'):
        fti[0]['immediate_view'] = klass.immediate_view

    if not IReferenceable.isImplementedByInstancesOf(klass):
        refs = findDict(fti[0]['actions'], 'id', 'references')
        refs['visible'] = False

    if not IExtensibleMetadata.isImplementedByInstancesOf(klass):
        refs = findDict(fti[0]['actions'], 'id', 'metadata')
        refs['visible'] = False

    # Set folder_listing to 'view' if the class implements ITemplateMixin
    if not ITemplateMixin.isImplementedByInstancesOf(klass):
        actions = []
        for action in fti[0]['actions']:
            if action['id'] != 'folderlisting':
                actions.append(action)
            else:
                action['action'] = 'string:${folder_url}/view'
                actions.append(action)
        fti[0]['actions'] = tuple(actions)

    # Remove folderlisting action from non folderish content types
    if not getattr(klass,'isPrincipiaFolderish', None):
        actions = []
        for action in fti[0]['actions']:
            if action['id'] != 'folderlisting':
                actions.append(action)
        fti[0]['actions'] = tuple(actions)

def process_types(types, pkg_name):
    content_types = ()
    constructors = ()
    ftis = ()

    for rti in types:
        typeName = rti['name']
        klass = rti['klass']
        module = rti['module']

        if hasattr(module, 'factory_type_information'):
            fti = module.factory_type_information
        else:
            fti = deepcopy(base_factory_type_information)
            modify_fti(fti, klass, pkg_name)

        # Add a callback to modifty the fti
        if hasattr(module, 'modify_fti'):
            module.modify_fti(fti[0])
        else:
            m = None
            for k in klass.__bases__:
                base_module = sys.modules[k.__module__]
                if hasattr(base_module, 'modify_fti'):
                    m = base_module
                    break
            if m is not None:
                m.modify_fti(fti[0])

        ctor = getattr(module, 'add%s' % typeName, None)
        if ctor is None:
            ctor = generateCtor(typeName, module)

        content_types += (klass,)
        constructors += (ctor,)
        ftis += fti

    return content_types, constructors, ftis

def _guessPackage(base):
    if base.startswith('Products'):
        base = base[9:]
        idx = base.index('.')
        if idx != -1:
            base = base[:idx]
    return base

def registerType(klass, package=None):
    assert IBaseObject.isImplementedByInstancesOf(klass), getDottedName(klass)
    if not package:
        package = _guessPackage(klass.__module__)

    # Registering a class results in classgen doing its thing
    # Set up accessor/mutators and sane meta/portal_type
    generateClass(klass)
    
    registerComponent(klass, package=package)


def fixAfterRenameType(context, old_portal_type, new_portal_type):
    """Helper method to fix some vars after renaming a type in portal_types

    It will raise an IndexError if called with a nonexisting old_portal_type.
    If you like to swallow the error please use a try/except block in your own
    code and do NOT 'fix' this method.
    """
    at_tool = getToolByName(context, TOOL_NAME)
    typeRegistry = getRegistry(IBaseObject)
    __traceback_info__ = (context, old_portal_type, new_portal_type,
                          [t['portal_type'] for t in typeRegistry.values()])
    # Will fail if old portal type wasn't registered (DO 'FIX' THE INDEX ERROR!)
    old_type = [t for t in typeRegistry.values()
                if t['portal_type'] == old_portal_type][0]

    # Rename portal type
    old_type['portal_type'] = new_portal_type

    # Copy old templates to new portal name without references
    old_templates = at_tool._templates.get(old_portal_type)
    at_tool._templates[new_portal_type] = deepcopy(old_templates)

def registerClasses(context, package, types=None):
    registered = listTypes(package)
    if types is not None:
        registered = filter(lambda t: t['meta_type'] in types, registered)
    for t in registered:
        module = t['module']
        typeName = t['name']
        meta_type = t['meta_type']
        portal_type = t['portal_type']
        klass = t['klass']
        ctorName = 'manage_add%s' % typeName
        constructor = getattr(module, ctorName, None)
        if constructor is None:
            constructor = generateZMICtor(typeName, module)
        addFormName = 'manage_add%sForm' % typeName
        setattr(module, addFormName,
                BoundPageTemplateFile('base_add.pt', _zmi,
                                      __name__=addFormName,
                                      extra={'constructor':ctorName,
                                             'type':meta_type,
                                             'package':package,
                                             'portal_type':portal_type}
                                      ))
        editFormName = 'manage_edit%sForm' % typeName
        setattr(klass, editFormName,
                BoundPageTemplateFile('base_edit.pt', _zmi,
                                      __name__=editFormName,
                                      extra={'handler':'processForm',
                                             'type':meta_type,
                                             'package':package,
                                             'portal_type':portal_type}
                                      ))

        position = False
        for item in klass.manage_options:
            if item['label'] != 'Contents':
                continue
            position += 1
        folderish = getattr(klass, 'isPrincipiaFolderish', position)
        options = list(klass.manage_options)
        options.insert(position, {'label' : 'Edit',
                                  'action' : editFormName
                                  })
        klass.manage_options = tuple(options)
        generatedForm = getattr(module, addFormName)
        icon = folderish and folder_icon or document_icon
        if klass.__dict__.has_key('content_icon'):
            icon = klass.content_icon
        elif hasattr(klass, 'factory_type_information'):
            factory_type_information = klass.factory_type_information
            if factory_type_information.has_key('content_icon'):
                icon = factory_type_information['content_icon']

        context.registerClass(
            t['klass'],
            constructors=(generatedForm, constructor),
            visibility=None,
            icon=icon
            )

def listTypes(package=None):
    typeRegistry = getRegistry(IBaseObject)
    values = typeRegistry.values()
    if package:
        values = [v for v in values if v['package'] == package]

    return values

def getType(name, package):
    key = "%s.%s" % (package, name)
    typeRegistry = getRegistry(IBaseObject)
    return typeRegistry[key]
