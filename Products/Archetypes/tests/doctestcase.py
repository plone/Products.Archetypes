# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################
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