# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and 
#	                       the respective authors. All rights reserved.
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

import os, sys

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

# Load fixture
from common import *
from utils import *
from Testing import ZopeTestCase

from Products.CMFCore.utils import getToolByName

class FunctionalTest(ZopeTestCase.Functional,
                     ArcheSiteTestCase):
    """Functional Tests for Archetypes"""


def test_suite():
    import unittest
    suite = unittest.TestSuite()
    from Testing.ZopeTestCase import doctest
    FileSuite = doctest.FunctionalDocFileSuite
    files = ['traversal.txt']
    for f in files:
        suite.addTest(FileSuite(f, test_class=FunctionalTest))
    return suite

if __name__ == '__main__':
    framework(descriptions=1, verbosity=1)

