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

#
# ArchetypesTestCase
#
# $Id$

from Testing import ZopeTestCase
from Products.CMFTestCase import CMFTestCase

DEPS = ('CMFCore', 'CMFDefault', 'CMFCalendar', 'CMFTopic',
        'DCWorkflow', 'CMFActionIcons', 'CMFQuickInstallerTool',
        'CMFFormController',  'ZCTextIndex', 'TextIndexNG2',
        'MailHost', 'PageTemplates', 'PythonScripts', 'ExternalMethod',
        )
DEPS_PLONE = ('GroupUserFolder', 'SecureMailHost', 'CMFPlone',)
DEPS_OWN = ('MimetypesRegistry', 'PortalTransforms', 'Marshall', 'Archetypes',
            'ArchetypesTestUpdateSchema',)

default_user = ZopeTestCase.user_name
default_role = 'Member'

# install products
for product in DEPS + DEPS_OWN:
    ZopeTestCase.installProduct(product)
CMFTestCase.setupCMFSite()

import time
from StringIO import StringIO
from Products.CMFTestCase.setup import portal_name, portal_owner
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_base
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.atapi import listTypes
from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes.Extensions.Install import install as installArchetypes
from Products.CMFCore.utils import getToolByName

class ArchetypesTestCase(ZopeTestCase.ZopeTestCase):
    '''Simple AT test case'''

class ArcheSiteTestCase(CMFTestCase.CMFTestCase):
    """AT test case inside a CMF site
    """
    def login(self, name=ZopeTestCase.user_name):
        '''Logs in.'''
        uf = self.getPortal().acl_users
        user = uf.getUserById(name)
        if not hasattr(user, 'aq_base'):
            user = user.__of__(uf)
        newSecurityManager(None, user)


def setupArchetypes(app, id=portal_name, quiet=0):
    '''Installs the Archetypes product into the portal.'''
    portal = app[id]
    user = app.acl_users.getUserById(portal_owner).__of__(app.acl_users)
    qi = getToolByName(portal, 'portal_quickinstaller', default=None)
    # install quick installer
    if qi is None:
        start = time.time()
        if not quiet: ZopeTestCase._print('Adding Quickinstaller Tool ... ')
        factory = portal.manage_addProduct['CMFQuickInstallerTool']
        newSecurityManager(None, user)
        factory.manage_addTool('CMF QuickInstaller Tool')
        noSecurityManager()
        get_transaction().commit()
        if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-start,))

    qi = getToolByName(portal, 'portal_quickinstaller')
    installed = qi.listInstallableProducts(skipInstalled=True)
    if 'CMFFormController' not in installed:
        start = time.time()
        if not quiet: ZopeTestCase._print('Adding CMFFormController ... ')
        # Login as portal owner
        newSecurityManager(None, user)
        # Install Archetypes
        qi.installProduct('CMFFormController')
        # Log out
        noSecurityManager()
        get_transaction().commit()
        if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-start,))

    if 'Archetypes' not in installed:
        start = time.time()
        if not quiet: ZopeTestCase._print('Adding Archetypes ... ')
        # Login as portal owner
        newSecurityManager(None, user)
        # Install Archetypes
        installArchetypes(portal, include_demo=1)
        # Log out
        noSecurityManager()
        get_transaction().commit()
        if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-start,))
    elif not hasattr(aq_base(portal.portal_types), 'SimpleBTreeFolder'):
        _start = time.time()
        if not quiet: ZopeTestCase._print('Adding Archetypes demo types ... ')
        # Login as portal owner
        newSecurityManager(None, user)
        # Install Archetypes
        out = StringIO()
        installTypes(portal, out, listTypes(PKG_NAME), PKG_NAME)
        # Log out
        noSecurityManager()
        get_transaction().commit()
        if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-_start,))

app = ZopeTestCase.app()
setupArchetypes(app)
ZopeTestCase.close(app)
