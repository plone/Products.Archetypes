import Zope # Sigh, make product initialization happen

try:
    Zope.startup()
except: # Zope > 2.6
    pass

from unittest import main
from Products.CMFCore.tests.base.utils import build_test_suite

def test_suite():

    return build_test_suite('Products.Archetypes.tests',[
        'test_baseschema',
        'test_baseunit',
        'test_classgen',
        'test_contenttype',
        'test_fields',
        'test_referenceable',
        'test_referenceEngine',
        'test_rename',
        'test_storage',
        'test_utils',
        'test_utils2',
        'test_schemata',
        'test_sitepolicy',
        'test_sqlstorage',
        'test_update_schema1',
        # 'test_update_schema2', # Can't run both together.
        'test_utils',
        'test_utils2',
        # 'test_widgets', # Run this one with care. It may harm your database.
        ])

if __name__ == '__main__':
    main(defaultTest='test_suite')
