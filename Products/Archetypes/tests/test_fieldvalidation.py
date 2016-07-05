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

from Acquisition import Explicit

from Products.Archetypes.atapi import Field, IntegerField
from Products.Archetypes.BaseObject import BaseObject
from Products.validation import validation as validationService
from Products.validation.interfaces.IValidator import IValidator
from zope.interface import implementer


@implementer(IValidator)
class MyValidator:

    def __init__(self, name, fun):
        self.name = name
        self.fun = fun

    def __call__(self, value, instance, field, *args, **kwargs):
        return self.fun(value)

# never validates
validationService.register(MyValidator('v1', lambda val: val))
# always validates
validationService.register(MyValidator('v2', lambda val: 1))
# never validates
validationService.register(MyValidator('v3', lambda val: []))

settings = [
    {'field': {},  # this is the dict of field properties
     'value': None,
     'assertion': lambda result: result is None,  # result of field.validate()
     },

    {'field': {'required': 1},  # required
     'value': None,  # ... but no value given
     'assertion': lambda result: result is not None},

]

for req in 0, 1:  # 0 == not required, 1 == required

    for validator in (('v2', 'v1'), ('v1',)):
        # Make sure that for both sets of validators, v1 returns an error.
        settings.append(
            {'field': {'required': req, 'validators': validator},
             'value': 'bass',
             'assertion': lambda result: result.find('bass') > -1}
        )

    # the trombone is in the vocabulary
    settings.append(
        {'field': {'required': req, 'enforceVocabulary': 1,
                   'vocabulary': ('frenchhorn', 'trombone', 'trumpet')},
         'value': 'trombone',
         'assertion': lambda result: result is None}
    )

    # tuba is not in vocabulary, so this must fail
    settings.append(
        {'field': {'required': req, 'enforceVocabulary': 1,
                   'vocabulary': ('frenchhorn', 'trombone', 'trumpet')},
         'value': 'tuba',
         'assertion': lambda result: result is not None}
    )

    # tuba is not in vocabulary, so this must fail
    settings.append(
        {'field': {'required': req, 'enforceVocabulary': 1,
                   'multiValued': 1,
                   'vocabulary': ('frenchhorn', 'trombone', 'trumpet')},
         'value': ('tuba', 'trombone'),
         'assertion': lambda result: result is not None}
    )

    # enforceVocabulary, but no vocabulary given
    settings.append(
        {'field': {'required': req, 'enforceVocabulary': 1},
         'value': 'cello',
         'assertion': lambda result: result is not None}
    )


class FakeType(Explicit, BaseObject):

    def unicodeEncode(self, v): return v  # don't


class TestSettings(ATTestCase):

    def afterSetUp(self):
        instance = FakeType('fake')
        self.instance = instance.__of__(self.folder)

    def testSettings(self):
        # tests every setting in global "settings"
        for setting in settings:
            field = Field('orchestra', **setting['field'])
            result = field.validate(setting['value'], self.instance, errors={})
            msg = 'Assertion failed for setting:\n%s.\nResult was "%s".' % \
                  (setting, result)

            self.assertTrue(setting['assertion'](result),
                            setting.get('failmsg', msg))


class TestValidation(ATTestCase):

    def afterSetUp(self):
        self.instance = FakeType('fake')

    def testIntegerZeroInvalid(self):
        # attach a validator that never validates, so any value must fail
        field = IntegerField('integer', validators=('v3',))

        self.assertTrue(field.validate(
            1, self.instance, errors={}) is not None)
        self.assertTrue(field.validate(
            0, self.instance, errors={}) is not None)
