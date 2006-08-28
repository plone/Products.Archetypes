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
import transaction
import sys, code

USELAYER=False

if not attestcase.USE_PLONETESTCASE:
    from Products.CMFTestCase import CMFTestCase
    from Products.CMFTestCase.setup import portal_name
    from Products.CMFTestCase.setup import portal_owner
    # setup a CMF site 
    CMFTestCase.setupCMFSite()
    PortalTestClass = CMFTestCase.CMFTestCase
else:
    import Products.PloneTestCase.setup
    from Products.PloneTestCase import PloneTestCase
    from Products.PloneTestCase.setup import portal_name
    from Products.PloneTestCase.setup import portal_owner
    # setup a Plone site 
    PloneTestCase.setupPloneSite()
    PortalTestClass = PloneTestCase.PloneTestCase
    USELAYER = Products.PloneTestCase.setup.USELAYER

class ATSiteTestCase(PortalTestClass, attestcase.ATTestCase):
    """AT test case inside a CMF site
    """
    
    __implements__ = PortalTestClass.__implements__ + \
                     attestcase.ATTestCase.__implements__

class ATFunctionalSiteTestCase(Functional, ATSiteTestCase):
    """AT test case for functional tests inside a CMF site
    """
    __implements__ = Functional.__implements__ + ATSiteTestCase.__implements__ 
    
    def interact(self, locals=None):
        """Provides an interactive shell aka console inside your testcase.
        
        It looks exact like in a doctestcase and you can copy and paste
        code from the shell into your doctest. The locals in the testcase are 
        available, becasue you are in the testcase.
    
        In your testcase or doctest you can invoke the shell at any point by
        calling::
            
            >>> interact( locals() )        
            
        locals -- passed to InteractiveInterpreter.__init__()
        """
        savestdout = sys.stdout
        sys.stdout = sys.stderr
        sys.stderr.write('\n'+'='*70)
        console = code.InteractiveConsole(locals)
        console.interact("""
DocTest Interactive Console - (c) BlueDynamics Alliance, Austria, 2006
Note: You have the same locals available as in your test-case. 
Ctrl-D ends session and continues testing.
""")
        sys.stdout.write('\nend of DocTest Interactive Console session\n')
        sys.stdout.write('='*70+'\n')
        sys.stdout = savestdout

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
        transaction.commit()
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
        transaction.commit()
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
        transaction.commit()
        if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-start,))

    if not hasattr(aq_base(portal.portal_types), 'SimpleBTreeFolder'):
        _start = time.time()
        if not quiet: ZopeTestCase._print('Adding Archetypes demo types ... ')
        # Login as portal owner
        newSecurityManager(None, user)
        # Install Archetypes
        out = StringIO()
        installTypes(portal, out, listTypes(PKG_NAME), PKG_NAME)
        # Log out
        noSecurityManager()
        transaction.commit()
        if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-_start,))

if USELAYER:
    from Products.PloneTestCase.utils import safe_load_site_wrapper
    setupArchetypes = safe_load_site_wrapper(setupArchetypes)  

# Install Archetypes
# XXX replace with layer
app = ZopeTestCase.app()
setupArchetypes(app)
ZopeTestCase.close(app)

__all__ = ('ATSiteTestCase', 'ATFunctionalSiteTestCase', 'portal_name',
           'portal_owner')
