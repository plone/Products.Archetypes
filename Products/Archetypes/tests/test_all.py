import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from unittest import main
from Products.CMFCore.tests.base.utils import build_test_suite

def test_suite():

    return build_test_suite('Products.Archetypes.tests',[
        'test_storage',
        'test_classgen',
        'test_baseschema',
        'test_utils'
        ])

if __name__ == '__main__':
    main(defaultTest='test_suite')
