import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.public import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.Storage import AttributeStorage, MetadataStorage
from Products.Archetypes import listTypes
from Products.Archetypes.Widget import IdWidget, StringWidget, BooleanWidget, \
     KeywordWidget, TextAreaWidget, CalendarWidget, SelectionWidget
from Products.Archetypes.utils import DisplayList
from Products.CMFCore  import CMFCorePermissions

from DateTime import DateTime
import unittest

content_type = BaseSchema 

class Dummy(BaseContent):
    type = content_type
    
   
class BaseSchemaTest( unittest.TestCase ):

    def setUp( self ):
        registerType(Dummy)
        content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)
        self._dummy = Dummy(oid='dummy')

    def test_id(self):
        dummy = self._dummy
        field = dummy.getField('id')

        self.failUnless(field.required == 1)
        self.failUnless(field.default == None)
        self.failUnless(field.searchable == 0)
        self.failUnless(field.vocabulary == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 0)
        self.failUnless(field.accessor == 'getId')
        self.failUnless(field.mutator == 'setId')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'veVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'object')
        self.failUnless(isinstance(field.storage, AttributeStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, IdWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())
                
    def test_title(self):
        dummy = self._dummy
        field = dummy.getField('title')

        self.failUnless(field.required == 1)
        self.failUnless(field.default == '')
        self.failUnless(field.searchable == 1)
        self.failUnless(field.vocabulary == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 0)
        self.failUnless(field.accessor == 'Title')
        self.failUnless(field.mutator == 'setTitle')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'veVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'object')
        self.failUnless(isinstance(field.storage, AttributeStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, StringWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    ### Metadata Properties

    def test_allowdiscussion(self):
        dummy = self._dummy
        field = dummy.getField('allowDiscussion')

        self.failUnless(field.required == 0)
        self.failUnless(field.default == 0)
        self.failUnless(field.searchable == 0)
        self.failUnless(field.vocabulary == DisplayList(((0, 'off'), (1, 'on'),
                                              (None, 'default'))))
        self.failUnless(field.enforceVocabulary == 1)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'isDiscussable')
        self.failUnless(field.mutator == 'allowDiscussion')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'object')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, BooleanWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(vocab == DisplayList(((0, 'off'), (1, 'on'),
                                              (None, 'default'))))

    def test_subject(self):
        dummy = self._dummy
        field = dummy.getField('subject')

        self.failUnless(field.required == 0)
        self.failUnless(field.default == [])
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 1)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Subject')
        self.failUnless(field.mutator == 'setSubject')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'lines')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, KeywordWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_description(self):
        dummy = self._dummy
        field = dummy.getField('description')

        self.failUnless(field.required == 0)
        self.failUnless(field.default == '')
        self.failUnless(field.searchable == 1)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Description')
        self.failUnless(field.mutator == 'setDescription')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'metadata')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, TextAreaWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_contributors(self):
        dummy = self._dummy
        field = dummy.getField('contributors')

        self.failUnless(field.required == 0)
        self.failUnless(field.default == [])
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Contributors')
        self.failUnless(field.mutator == 'setContributors')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'lines')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, LinesWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_effectivedate(self):
        dummy = self._dummy
        field = dummy.getField('effective_date')

        self.failUnless(field.required == 0)
        self.failUnless(field.default is None)
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'EffectiveDate')
        self.failUnless(field.mutator == 'setEffectiveDate')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'lines')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, CalendarWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_effectivedate(self):
        dummy = self._dummy
        field = dummy.getField('effectiveDate')

        self.failUnless(field.required == 0)
        self.failUnless(field.default is None)
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'EffectiveDate')
        self.failUnless(field.mutator == 'setEffectiveDate')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'datetime')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, CalendarWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_expirationdate(self):
        dummy = self._dummy
        field = dummy.getField('expirationDate')

        self.failUnless(field.required == 0)
        self.failUnless(field.default is None)
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'ExpirationDate')
        self.failUnless(field.mutator == 'setExpirationDate')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'datetime')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, CalendarWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def test_language(self):
        dummy = self._dummy
        field = dummy.getField('language')

        self.failUnless(field.required == 0)
        self.failUnless(field.default == 'en')
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == 'languages')
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Language')
        self.failUnless(field.mutator == 'setLanguage')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'metadata')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, SelectionWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(vocab == dummy.languages())

    def test_rights(self):
        dummy = self._dummy
        field = dummy.getField('rights')

        self.failUnless(field.required == 0)
        self.failUnless(field.default is None)
        self.failUnless(field.searchable == 0)
        vocab = field.vocabulary
        self.failUnless(vocab == ())
        self.failUnless(field.enforceVocabulary == 0)
        self.failUnless(field.multiValued == 0)
        self.failUnless(field.isMetadata == 1)
        self.failUnless(field.accessor == 'Rights')
        self.failUnless(field.mutator == 'setRights')
        self.failUnless(field.read_permission == CMFCorePermissions.View)
        self.failUnless(field.write_permission == CMFCorePermissions.ModifyPortalContent)
        self.failUnless(field.form_info is None)
        self.failUnless(field.generateMode == 'mVc')
        self.failUnless(field.force == '')
        self.failUnless(field.type == 'metadata')
        self.failUnless(isinstance(field.storage, MetadataStorage))
        self.failUnless(field.validators == ())
        self.failUnless(isinstance(field.widget, TextAreaWidget))
        vocab = field.Vocabulary(dummy)
        self.failUnless(isinstance(vocab, DisplayList))
        self.failUnless(tuple(vocab) == ())

    def tearDown( self ):
        del self._dummy
        
def test_suite():
    return unittest.TestSuite((
        unittest.makeSuite(BaseSchemaTest),
        ))

if __name__ == '__main__':
    unittest.main()
