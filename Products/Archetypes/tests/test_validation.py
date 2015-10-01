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

from Products.Archetypes.tests.attestcase import ATTestCase

from Products.validation import validation as validationService


class TestValidation(ATTestCase):

    def test_inNumericRange(self):
        v = validationService.validatorFor('inNumericRange')
        self.assertEqual(v(10, 1, 20), 1)
        self.assertEqual(v('10', 1, 20), 1)
        self.assertNotEqual(v(0, 4, 5), 1)

    def test_isPrintable(self):
        v = validationService.validatorFor('isPrintable')
        self.assertEqual(v('text'), 1)
        self.assertNotEqual(v('\u203'), 1)
        self.assertNotEqual(v(10), 1)

    def test_isSSN(self):
        v = validationService.validatorFor('isSSN')
        self.assertEqual(v('111223333'), 1)
        self.assertEqual(v('111-22-3333', ignore=r'-'), 1)

    def test_isUSPhoneNumber(self):
        v = validationService.validatorFor('isUSPhoneNumber')
        self.assertEqual(v('(212) 555-1212',
                           ignore=r'[\s\(\)\-]'), 1)
        self.assertEqual(v('2125551212',
                           ignore=r'[\s\(\)\-]'), 1)

        self.assertEqual(v('(212) 555-1212'), 1)

    def test_isURL(self):
        v = validationService.validatorFor('isURL')
        self.assertEqual(v('http://foo.bar:8080/manage'), 1)
        self.assertNotEqual(v('http://\n'), 1)
        self.assertNotEqual(v('../foo/bar'), 1)

    def test_isEmail(self):
        v = validationService.validatorFor('isEmail')
        self.assertEqual(v('test@test.com'), 1)
        self.assertNotEqual(v('@foo.bar'), 1)
        self.assertNotEqual(v('me'), 1)

    def test_isUnixLikeName(self):
        v = validationService.validatorFor('isUnixLikeName')
        self.assertEqual(v('abcd'), 1)
        self.assertEqual(v('a_123456'), 1)
        self.assertNotEqual(v('123'), 1)
        self.assertNotEqual(v('ab.c'), 1)
        self.assertNotEqual(v('ab,c'), 1)
        self.assertNotEqual(v('aaaaaaaab'), 1)  # too long
