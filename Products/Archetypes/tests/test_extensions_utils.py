
from cStringIO import StringIO

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
#from Products.Archetypes.tests.utils import makeContent
from Products.Archetypes.examples.ComplexType import ComplexType
from Products.Archetypes.Extensions import utils

ComplexType.installMode = ('indexes', )
class InstallIndexesTests(ATSiteTestCase):

    def tearDown(self):
        ATSiteTestCase.tearDown(self)
        del ComplexType.schema['richtextfield'].index
        try:
            del ComplexType.schema['richtextfield'].index_method
        except (AttributeError, KeyError):
            pass

    def test_base_usage(self):
        ComplexType.schema['richtextfield'].index = 'FieldIndex'
        utils.install_indexes(self.portal, StringIO(), (ComplexType,) )
        self.failUnless('getRichtextfield' in self.portal.portal_catalog.indexes())


    def test_index_method(self):
        ComplexType.schema['richtextfield'].index = 'FieldIndex'
        ComplexType.schema['richtextfield'].index_method = 'Whatever'
        utils.install_indexes(self.portal, StringIO(), (ComplexType,) )
        self.failUnless('Whatever' in self.portal.portal_catalog.indexes())

        ComplexType.schema['richtextfield'].index_method = '_at_accessor'
        utils.install_indexes(self.portal, StringIO(), (ComplexType,) )
        self.failUnless('getRichtextfield' in self.portal.portal_catalog.indexes())

        ComplexType.schema['richtextfield'].index_method = '_at_edit_accessor'
        utils.install_indexes(self.portal, StringIO(), (ComplexType,) )
        self.failUnless('getRawRichtextfield' in self.portal.portal_catalog.indexes())


    def test_bad_index_method(self):
        ComplexType.schema['richtextfield'].index = 'FieldIndex'
        ComplexType.schema['richtextfield'].index_method = lambda x: 'yop'
        self.failUnlessRaises(ValueError,
                              utils.install_indexes, self.portal, StringIO(), (ComplexType,) )
        ComplexType.schema['richtextfield'].index_method = lambda x: 'yop'
        self.failUnlessRaises(ValueError,
                              utils.install_indexes, self.portal, StringIO(), (ComplexType,) )

        ComplexType.schema['richtextfield'].index_method = ComplexType._get_selection_vocab
        self.failUnlessRaises(ValueError,
                              utils.install_indexes, self.portal, StringIO(), (ComplexType,) )


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(InstallIndexesTests))
    return suite
