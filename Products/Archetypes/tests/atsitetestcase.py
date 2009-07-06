from Testing.ZopeTestCase import Functional

from Products.CMFTestCase import CMFTestCase
from Products.CMFTestCase.setup import portal_name
from Products.CMFTestCase.setup import portal_owner
from Products.CMFTestCase.setup import default_user

from Products.Archetypes.tests import attestcase
from Products.Archetypes.tests.layer import ArchetypesSite


class ATSiteTestCase(CMFTestCase.CMFTestCase, attestcase.ATTestCase):
    """AT test case with CMF site
    """
    layer = ArchetypesSite


class ATFunctionalSiteTestCase(Functional, ATSiteTestCase):
    """AT test case for functional tests with CMF site
    """
    layer = ArchetypesSite
