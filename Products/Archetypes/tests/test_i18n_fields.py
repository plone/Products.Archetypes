import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import * 

from Products.Archetypes.Field import *

class SiteProperties:
    default_charset = 'UTF-8'
    def getProperty(self, name, default=None):
        return getattr(self, name, default)
    
class PortalProperties:
    site_properties = SiteProperties()

class Dummy:
    portal_properties = PortalProperties()
    def getContentLanguage(self, lang):
        return lang or 'en'
    
instance = Dummy()

class I18NFieldTest( ArchetypesTestCase ):

    def test_get(self):
        f = I18NStringField('test')
        f.set(instance, 'english words', 'en')
        f.set(instance, 'mots fran\xc3\xa7ais', 'fr')
        self.assertEquals(f.get(instance), 'english words')
        self.assertEquals(f.get(instance, 'en'), 'english words')
        self.assertEquals(f.get(instance, 'fr'), 'mots fran\xc3\xa7ais')
        

    def test_getRaw(self):
        f = I18NStringField('test')
        f.set(instance, 'english words', 'en')
        f.set(instance, 'mots fran\xc3\xa7ais', 'fr')
        self.assertEquals(f.getRaw(instance), 'english words')
        self.assertEquals(f.getRaw(instance, 'en'), 'english words')
        self.assertEquals(f.getRaw(instance, 'fr'), 'mots fran\xc3\xa7ais')
        
    def test_unset(self):
        f = I18NStringField('test')
        f.set(instance, 'english words', 'en')
        f.set(instance, 'mots fran\xc3\xa7ais', 'fr')
        f.unset(instance, 'en')
        self.assertEquals(f.getRaw(instance, 'en'), '')
        self.assertEquals(f.getRaw(instance, 'fr'), 'mots fran\xc3\xa7ais')
        f.unset(instance, 'fr')
        self.assertEquals(f.getRaw(instance, 'en'), '')
        self.assertEquals(f.getRaw(instance, 'fr'), '')

            
if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(I18NFieldTest))
        return suite 
