#
# ArchetypesTestCase
#
# $Id: ArchetypesTestCase.py,v 1.5.16.7 2004/07/07 15:53:44 shh42 Exp $

from Testing import ZopeTestCase

ZopeTestCase.installProduct('CMFCore', 1)
ZopeTestCase.installProduct('CMFDefault', 1)
ZopeTestCase.installProduct('CMFCalendar', 1)
ZopeTestCase.installProduct('CMFTopic', 1)
ZopeTestCase.installProduct('DCWorkflow', 1)
ZopeTestCase.installProduct('CMFActionIcons', 1)
ZopeTestCase.installProduct('CMFQuickInstallerTool', 1)
ZopeTestCase.installProduct('CMFFormController', 1)
ZopeTestCase.installProduct('GroupUserFolder', 1)
ZopeTestCase.installProduct('ZCTextIndex', 1)
ZopeTestCase.installProduct('TextIndexNG2', 1)
ZopeTestCase.installProduct('SecureMailHost', 1)
ZopeTestCase.installProduct('CMFPlone', 1)
ZopeTestCase.installProduct('MailHost', 1)
ZopeTestCase.installProduct('PageTemplates', 1)
ZopeTestCase.installProduct('PythonScripts', 1)
ZopeTestCase.installProduct('ExternalMethod', 1)
# Archetypes dependencies
ZopeTestCase.installProduct('MimetypesRegistry', 1)
ZopeTestCase.installProduct('PortalTransforms', 1)
ZopeTestCase.installProduct('Archetypes', 1)
ZopeTestCase.installProduct('ArchetypesTestUpdateSchema', 1)

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_base
import time
from StringIO import StringIO

default_user = ZopeTestCase.user_name
default_role = 'Member'


from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.public import listTypes
from Products.Archetypes.Extensions.utils import installTypes


class ArchetypesTestCase(ZopeTestCase.ZopeTestCase):
    '''Simple AT test case'''


try:
    from Products.CMFPlone.tests import PloneTestCase
except ImportError:
    pass # No Plone?
else:
    from Products.Archetypes.Extensions.Install import install as installArchetypes

    portal_name = PloneTestCase.portal_name
    portal_owner = PloneTestCase.portal_owner

    class ArcheSiteTestCase(PloneTestCase.PloneTestCase):
        '''AT test case with Plone site'''

        def getPortal(self):
            '''Returns the portal object to the bootstrap code.
               You should NOT call this method but use the 
               self.portal attribute to access the site object.
            '''
            return PloneTestCase.PloneTestCase.getPortal(self)
        
        def getPermissionsOfRole(self, role):
            perms = self.portal.permissionsOfRole(role)
            return [p['name'] for p in perms if p['selected']]

        def _setup(self):
            '''Extends the portal setup.'''
            PloneTestCase.PloneTestCase._setup(self)
            # Add a manager user
            uf = self.portal.acl_users
            uf._doAddUser('manager', 'secret', ['Manager'], [])

        # XXX Don't break third party tests

        def getManagerUser(self):
            # b/w compat
            uf = self.portal.acl_users
            return uf.getUserById('manager').__of__(uf)

        def getMemberUser(self):
            # b/w compat
            uf = self.portal.acl_users
            return uf.getUserById(default_user).__of__(uf)


    def setupArchetypes(app, id=portal_name, quiet=0):
        '''Installs the Archetypes product into the portal.'''
        portal = app[id]
        if not hasattr(aq_base(portal), 'archetype_tool'):
            _start = time.time()
            if not quiet: ZopeTestCase._print('Adding Archetypes ... ')
            # Login as portal owner
            user = app.acl_users.getUserById(portal_owner).__of__(app.acl_users)
            newSecurityManager(None, user)
            # Install Archetypes
            installArchetypes(portal, include_demo=1)
            # Log out
            noSecurityManager()
            get_transaction().commit()
            if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-_start,))
        elif not hasattr(aq_base(portal.portal_types), 'DDocument'):
            _start = time.time()
            if not quiet: ZopeTestCase._print('Adding Archetypes demo types ... ')
            # Login as portal owner
            user = app.acl_users.getUserById(portal_owner).__of__(app.acl_users)
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
