import os
import sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

import unittest
from zope.testing.doctestunit import DocFileSuite
from zope.app.tests import ztapi, placelesssetup
from zope.interface import classImplements

from Products.Archetypes.interfaces import ILock
from Products.Archetypes.interfaces import ITTWLockable
from Products.Archetypes.adapters import TTWLock
from Products.Archetypes.BaseObject import BaseObject

def setUp(test):
    placelesssetup.setUp(test)
    classImplements(BaseObject, ITTWLockable)
    ztapi.provideAdapter(ITTWLockable, ILock,
                         TTWLock)

def test_suite():
    return unittest.TestSuite((
        DocFileSuite('locking.txt',
                     package='Products.Archetypes.docs',
                     setUp=setUp,
                     tearDown=placelesssetup.tearDown),
        ))

if __name__ == '__main__':
    unittest.main(defaultTest='test_suite')
