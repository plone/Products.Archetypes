
from Testing.ZopeTestCase import utils
from Products.Archetypes.tests import attestcase

if not attestcase.USE_PLONETESTCASE:
    from Products.CMFTestCase.layer import CMFSite as BaseLayer
else:
    from Products.PloneTestCase.layer import PloneSite as BaseLayer


class ATSite(BaseLayer):

    def setUp(cls):
        # Avoid import loop
        from Products.Archetypes.tests.atsitetestcase import setupArchetypes
        utils.appcall(setupArchetypes, quiet=1)
    setUp = classmethod(setUp)

    def tearDown(cls):
        # Remove demo types?
        pass
    tearDown = classmethod(tearDown)

