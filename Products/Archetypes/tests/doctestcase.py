"""
"""
__author__ = 'Christian Heimes'
__docformat__ = 'restructuredtext'

##
# ZopeDocTestSuite
##
import warnings
import unittest

from Testing.ZopeTestCase.base import TestCase
from Testing.ZopeTestCase.ZopeTestCase import ZopeTestCase
from Testing.ZopeTestCase.doctest import doctest
from Testing.ZopeTestCase import interfaces as ztc_interfaces

# assign __module__ var to ExtensionClass - otherwise doctest import may fail
import ExtensionClass
ExtensionClass.Base.__module__ = ExtensionClass
ExtensionClass.ExtensionClass.__module__ = ExtensionClass

def ZopeDocTestSuite(*modules, **kw):
    """Based on Sid's FunctionalDocFileSuite
    """
    test_class = kw.get('test_class', ZopeTestCase)
    suite = kw.get('suite', None)
    suite_class = kw.get('suite_class', unittest.TestSuite)

    for var in ('test_class', 'suite', 'suite_class',):
        if var in kw:
            del kw[var]

    # If the passed-in test_class doesn't subclass base.TestCase,
    # we mix it in for you, but we will issue a warning.
    if not issubclass(test_class, TestCase):
        name = test_class.__name__
        warnings.warn(("The test_class you are using doesn't "
                       "subclass from base.TestCase. "
                       "Please fix that."), UserWarning, 2)
        if not 'ZDT' in name:
            name = 'ZDT%s' % name
        test_class = type(name, (TestCase, test_class), {})

    # If the test_class does not have a runTest attribute, 
    # we add one.
    #if not hasattr(test_class, 'runTest'):
    setattr(test_class, 'runTest', None)

    # Create a TestCase instance which will be used
    # to execute the setUp and tearDown methods, as well as
    # be passed into the test globals as 'self'.
    test_instance = test_class()

    # setUp
    kwsetUp = kw.get('setUp')
    def setUp(test):
        test_instance.setUp()
        test.globs['test'] = test
        test.globs['self'] = test_instance
        test.globs['app'] = test_instance.app
        if ztc_interfaces.IPortalTestCase.isImplementedBy(test_instance):
            test.globs['portal'] = test_instance.getPortal()
        if kwsetUp is not None:
            kwsetUp(test_instance)

    kw['setUp'] = setUp
    
    # tearDown
    kwtearDown = kw.get('tearDown')
    def tearDown(test):
        if kwtearDown is not None:
            kwtearDown(test_instance)
        test_instance.tearDown()

    kw['tearDown'] = tearDown
    
    # other options
    if 'optionflags' not in kw:
        kw['optionflags'] = (doctest.ELLIPSIS
                             | doctest.NORMALIZE_WHITESPACE)

    if suite is None:
        suite = suite_class()

    for module in modules:
        suite.addTest(doctest.DocTestSuite(module, **kw))

    return suite

__all__ = ('ZopeDocTestSuite',)