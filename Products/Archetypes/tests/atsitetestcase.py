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
__author__ = "Christian Heimes"

from Testing import ZopeTestCase

from Testing.ZopeTestCase.functional import Functional
from Products.Archetypes.tests import attestcase
from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_base

if not attestcase.USE_PLONETESTCASE:
    from Products.CMFTestCase import CMFTestCase
    from Products.CMFTestCase.setup import portal_name
    from Products.CMFTestCase.setup import portal_owner
    # setup a CMF site
    CMFTestCase.setupCMFSite()
    PortalTestClass = CMFTestCase.CMFTestCase
else:
    from Products.PloneTestCase import PloneTestCase
    from Products.PloneTestCase.setup import portal_name
    from Products.PloneTestCase.setup import portal_owner
    # setup a Plone site
    PloneTestCase.setupPloneSite()
    PortalTestClass = PloneTestCase.PloneTestCase

class ATSiteTestCase(PortalTestClass, attestcase.ATTestCase):
    """AT test case inside a CMF site
    """

    __implements__ = PortalTestClass.__implements__ + \
                     attestcase.ATTestCase.__implements__

    def login(self, name=ZopeTestCase.user_name):
        '''Logs in.'''
        uf = self.getPortal().acl_users
        user = uf.getUserById(name)
        if not hasattr(user, 'aq_base'):
            user = user.__of__(uf)
        newSecurityManager(None, user)

    # XXX Don't break third party tests

    def getPermissionsOfRole(self, role):
        perms = self.portal.permissionsOfRole(role)
        return [p['name'] for p in perms if p['selected']]

    def _setup(self):
        '''Extends the portal setup.'''
        # BBB remove in AT 1.4
        PortalTestClass._setup(self)
        # Add a manager user
        uf = self.portal.acl_users
        uf._doAddUser('manager', 'secret', ['Manager'], [])

    def getManagerUser(self):
        # BBB remove in AT 1.4
        # b/w compat
        uf = self.portal.acl_users
        return uf.getUserById('manager').__of__(uf)

    def getMemberUser(self):
        # BBB remove in AT 1.4
        # b/w compat
        uf = self.portal.acl_users
        return uf.getUserById(default_user).__of__(uf)


class ATFunctionalSiteTestCase(Functional, ATSiteTestCase):
    """AT test case for functional tests inside a CMF site
    """
    __implements__ = Functional.__implements__ + ATSiteTestCase.__implements__

###
# Setup an archetypes site
###

import time
from StringIO import StringIO

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.atapi import listTypes
from Products.Archetypes.Extensions.utils import installTypes
from Products.Archetypes.Extensions.Install import install as installArchetypes


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

    if 'Eventually' not in installed:
        start = time.time()
        if not quiet: ZopeTestCase._print('Adding Eventually (Event Service) ... ')
        # Login as portal owner
        newSecurityManager(None, user)
        # Install Archetypes
        qi.installProduct('Eventually')
        # Log out
        noSecurityManager()
        get_transaction().commit()
        if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-start,))

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

# Install Archetypes
app = ZopeTestCase.app()
setupArchetypes(app)
ZopeTestCase.close(app)

__all__ = ('ATSiteTestCase', 'ATFunctionalSiteTestCase', 'portal_name',
           'portal_owner')
