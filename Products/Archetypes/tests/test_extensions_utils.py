from cStringIO import StringIO

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.examples.ComplexType import ComplexType
from Products.Archetypes.Extensions import utils

ComplexType.installMode = ('indexes',)


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
        utils.install_indexes(self.portal, StringIO(), (ComplexType,))
        self.assertTrue(
            'getRichtextfield' in self.portal.portal_catalog.indexes())

    def test_index_method(self):
        ComplexType.schema['richtextfield'].index = 'FieldIndex'
        ComplexType.schema['richtextfield'].index_method = 'Whatever'
        utils.install_indexes(self.portal, StringIO(), (ComplexType,))
        self.assertTrue('Whatever' in self.portal.portal_catalog.indexes())

        ComplexType.schema['richtextfield'].index_method = '_at_accessor'
        utils.install_indexes(self.portal, StringIO(), (ComplexType,))
        self.assertTrue(
            'getRichtextfield' in self.portal.portal_catalog.indexes())

        ComplexType.schema['richtextfield'].index_method = '_at_edit_accessor'
        utils.install_indexes(self.portal, StringIO(), (ComplexType,))
        self.assertTrue(
            'getRawRichtextfield' in self.portal.portal_catalog.indexes())

    def test_bad_index_method(self):
        ComplexType.schema['richtextfield'].index = 'FieldIndex'
        ComplexType.schema['richtextfield'].index_method = lambda x: 'yop'
        self.assertRaises(ValueError,
                          utils.install_indexes, self.portal, StringIO(), (ComplexType,))
        ComplexType.schema['richtextfield'].index_method = lambda x: 'yop'
        self.assertRaises(ValueError,
                          utils.install_indexes, self.portal, StringIO(), (ComplexType,))

        ComplexType.schema[
            'richtextfield'].index_method = ComplexType._get_selection_vocab
        self.assertRaises(ValueError,
                          utils.install_indexes, self.portal, StringIO(), (ComplexType,))
