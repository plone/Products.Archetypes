#
# ArchetypesTestCase
#
# $Id: ArchetypesTestCase.py,v 1.5.16.1 2004/05/13 15:59:16 shh42 Exp $

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
ZopeTestCase.installProduct('CMFPlone', 1)
ZopeTestCase.installProduct('MailHost', 1)
ZopeTestCase.installProduct('PageTemplates', 1)
ZopeTestCase.installProduct('PythonScripts', 1)
ZopeTestCase.installProduct('ExternalMethod', 1)

ZopeTestCase.installProduct('Archetypes', 1)
ZopeTestCase.installProduct('PortalTransforms', 1)
ZopeTestCase.installProduct('ArchetypesTestUpdateSchema', 1)

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_base
import time

default_user = ZopeTestCase.user_name
default_role = 'Member'


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

        def _setup(self):
            '''Extends the portal setup.'''
            PloneTestCase.PloneTestCase._setup(self)
            # Add a manager user
            uf = self.portal.acl_users
            uf._doAddUser('manager', 'secret', ['Manager'], [])

    def setupArchetypes(app, id=portal_name, quiet=0):
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

    app = ZopeTestCase.app()
    setupArchetypes(app)
    ZopeTestCase.close(app)
