import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

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

class I18NFieldText( unittest.TestCase ):

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

            
def test_suite():
    return unittest.TestSuite([unittest.makeSuite(I18NFieldText)])

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
