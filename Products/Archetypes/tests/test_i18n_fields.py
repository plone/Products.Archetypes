import unittest

import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from Products.Archetypes.Field import *


class Dummy:
    def getContentLanguage(self, lang):
        return lang or 'en'
    
instance = Dummy()

class I18NFieldText( unittest.TestCase ):

    def test_get(self):
        f = I18NStringField('test')
        f.set(instance, 'english words', 'en')
        f.set(instance, 'mots français', 'fr')
        self.assertEquals(f.get(instance), 'english words')
        self.assertEquals(f.get(instance, 'en'), 'english words')
        self.assertEquals(f.get(instance, 'fr'), 'mots français')
        

    def test_getRaw(self):
        f = I18NStringField('test')
        f.set(instance, 'english words', 'en')
        f.set(instance, 'mots français', 'fr')
        self.assertEquals(f.getRaw(instance), 'english words')
        self.assertEquals(f.getRaw(instance, 'en'), 'english words')
        self.assertEquals(f.getRaw(instance, 'fr'), 'mots français')
        
    def test_unset(self):
        f = I18NStringField('test')
        f.set(instance, 'english words', 'en')
        f.set(instance, 'mots français', 'fr')
        f.unset(instance, 'en')
        self.assertEquals(f.getRaw(instance, 'en'), '')
        self.assertEquals(f.getRaw(instance, 'fr'), 'mots français')
        f.unset(instance, 'fr')
        self.assertEquals(f.getRaw(instance, 'en'), '')
        self.assertEquals(f.getRaw(instance, 'fr'), '')

            
def test_suite():
    return unittest.TestSuite([unittest.makeSuite(I18NFieldText)])

if __name__=='__main__':
    unittest.main(defaultTest='test_suite')
