##########################################################################
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
##########################################################################

from unittest import TestSuite, makeSuite

import os
import glob

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import PACKAGE_HOME
from Products.Archetypes.tests.utils import normalize_html
from Products.Archetypes.atapi import BaseUnit
from Products.Archetypes.tests.test_classgen import Dummy
from Products.Archetypes.tests.test_classgen import gen_dummy


class BaseUnitTest(ATSiteTestCase):

    def testSame(self):
        gen_dummy()
        # The BaseUnit expects 'instance' to be
        # acquisition wrapped, or else it does return
        # the untransformed text -- this was introduced
        # for compatibility with APE.
        parent = Dummy(oid='parent')
        dummy = Dummy(oid='dummy', init_transforms=1).__of__(parent)
        input = open(self.input)
        bu = BaseUnit(name='test', file=input,
                      mimetype='text/restructured',
                      instance=dummy)
        input.close()
        got = normalize_html(bu.transform(dummy, 'text/html'))

        try:
            output = open(self.output)
        except IOError:
            print "Creating %s" % self.output
            output = open(self.output, 'w')
            output.write(got)
            output.close()

        output = open(self.output)
        expected = normalize_html(output.read())
        output.close()

        self.assertEqual(got, expected)

tests = []

input_files = glob.glob(os.path.join(PACKAGE_HOME, "input", "rest*.rst"))
for f in input_files:
    fname = os.path.split(f)[1]
    outname = os.path.join(PACKAGE_HOME, "output",
                           '%s.out' % fname.split('.')[0])

    class BaseUnitTestSubclass(BaseUnitTest):
        input = f
        output = outname

    tests.append(BaseUnitTestSubclass)


def test_suite():
    suite = TestSuite()
    for test in tests:
        suite.addTest(makeSuite(test))
    return suite
