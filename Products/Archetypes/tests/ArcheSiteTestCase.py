#
# ArcheSiteTestCase
#

# $Id: ArcheSiteTestCase.py,v 1.2.24.1 2004/05/07 17:25:16 shh42 Exp $

from Testing import ZopeTestCase
from Products.CMFPlone.tests import PloneTestCase

from AccessControl.SecurityManagement import newSecurityManager
from AccessControl.SecurityManagement import noSecurityManager
from Acquisition import aq_base
import time

from Products.Archetypes.Extensions.Install import install as installArchetypes

portal_name = PloneTestCase.portal_name


class ArcheSiteTestCase(PloneTestCase.PloneTestCase):
    """ archetypes test case with plone site """

    def getManagerUser(self):
        uf = self.portal.acl_users
        return uf.getUserById('PloneManager').__of__(uf)

    def getMemberUser(self):
        uf = self.portal.acl_users
        return uf.getUserById('PloneMember').__of__(uf)


def setupArchetypes(app, id=portal_name, quiet=0):
    portal = app[id]
    if not hasattr(aq_base(portal), 'archetype_tool'):
        get_transaction().begin()
        _start = time.time()
        if not quiet: ZopeTestCase._print('Adding Archetypes ... ')

        uf = portal.acl_users
        # setup
        uf._doAddUser('PloneMember', '', ['Member'], [])
        uf._doAddUser('PloneManager', '', ['Manager'], [])
        # login as manager
        user = uf.getUserById('PloneManager').__of__(uf)
        newSecurityManager(None, user)
        # add Archetypes
        installArchetypes(portal, include_demo=1)
        # Log out
        noSecurityManager()
        get_transaction().commit()
        if not quiet: ZopeTestCase._print('done (%.3fs)\n' % (time.time()-_start,))


app = ZopeTestCase.app()
setupArchetypes(app)
ZopeTestCase.close(app)
