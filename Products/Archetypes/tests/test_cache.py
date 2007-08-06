from zope import component
from zope.annotation import IAnnotations

from Products.Archetypes.interfaces import ITransformCache
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import gen_class
from Products.Archetypes.tests.test_classgen import gen_dummy

class CacheTest(ATSiteTestCase):

    def afterSetUp(self):
        gen_dummy()
        dummy = Dummy(oid='dummy')
        self.folder._setObject('dummy', dummy)
        self.folder.dummy.initializeArchetype()
        self.dummy = self.folder.dummy

    def test_no_cache_annotation(self):
        # We don't want to create any persistent dicts if the dummy
        # type has merely been created:
        ann = IAnnotations(self.dummy)
        self.failIf('Products.Archetypes:transforms-cache' in ann,
                    "transforms-cache dict found in annotations.")

    def test_index_file_only_creates_file_field_cache_dict(self):
        self.dummy.setAfilefield('Text', mimetype='text/html')
        ffield = self.dummy.getField('afilefield')
        self.assertEquals(ffield.getIndexable(self.dummy), 'Text')

        cache = IAnnotations(self.dummy)['Products.Archetypes:transforms-cache']
        self.assertEquals(cache.keys(), ['afilefield'])
        self.assertEquals(cache['afilefield'].values(), ['Text'])

    def test_index_non_transformable_file_doesnt_create_annotation(self):
        self.dummy.setAfilefield('Bytes', mimetype='application/octet-stream')
        ffield = self.dummy.getField('afilefield')
        self.assertEquals(ffield.getIndexable(self.dummy), None)
        self.test_no_cache_annotation()

    def test_indexed_overwite_with_empty(self):
        self.dummy.setAfilefield('Old Text', mimetype='text/html')
        ffield = self.dummy.getField('afilefield')

        self.dummy.setAfilefield('', mimetype='text/html')
        self.assertEquals(ffield.getIndexable(self.dummy), None)
        
    def test_clear_cache(self):
        self.dummy.setAfilefield('Text', mimetype='text/html')
        ffield = self.dummy.getField('afilefield')
        self.assertEquals(ffield.getIndexable(self.dummy), 'Text')
        
        cache = IAnnotations(self.dummy)['Products.Archetypes:transforms-cache']
        self.assertEquals(cache.keys(), ['afilefield'])

        attool = self.portal.archetype_tool
        attool.clear_cache(self.dummy)
        self.assertEquals(cache.keys(), [])

    def test_clear_cache_all(self):
        dummy1 = self.dummy
        dummy2 = Dummy(oid='dummy')
        self.folder._setObject('dummy2', dummy2)
        self.folder.dummy2.initializeArchetype()

        for d in (dummy1, dummy2):
            d.setAfilefield('Spam', mimetype='text/html')
            d.getField('afilefield').getIndexable(d)
            cache = IAnnotations(d)['Products.Archetypes:transforms-cache']
            self.assertEquals(cache.keys(), ['afilefield'])

        attool = self.portal.archetype_tool
        attool.manage_clear_cache_all()

        for d in (dummy1, dummy2):
            self.assertEquals(cache.keys(), [])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(CacheTest))
    return suite
