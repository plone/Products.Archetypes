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
from types import StringType, TupleType, ListType, UnicodeType

from Products.Archetypes.interfaces.validation import IValidator
from Products.Archetypes.interfaces.validation import IValidationChain
from Products.Archetypes.validation.service import validationService
from Products.Archetypes.exceptions import UnknowValidatorError
from Products.Archetypes.exceptions import FalseValidatorError
from Products.Archetypes.exceptions import AlreadyRegisteredValidatorError

from types import StringTypes

V_REQUIRED   = 1
V_SUFFICIENT = 2


class ValidationChain:
    """
    """
    __implements__ = IValidationChain

    def __init__(self, name, title='', description='', validators=(),
                 register=False):
        self.name = name
        self.title = title or name
        self.description = description
        self._v_mode = []
        self._chain = []

        if type(validators) not in (TupleType, ListType):
            validators = (validators, )
        for validator in validators:
            if type(validator) in (TupleType, ListType):
                self.append(validator[0], validator[1])
            else:
                self.appendRequired(validator)

        if register:
            validationService.register(self)

    def __repr__(self):
        """print obj support
        """
        map = { V_REQUIRED : 'V_REQUIRED', V_SUFFICIENT : 'V_SUFFICIENT' }
        val = []
        for validator, mode in self:
            name = validator.name
            val.append("('%s', %s)" % (name, map.get(mode)))
        return '(%s)' % ', '.join(val)

    def __len__(self):
        """len(obj) suppor
        """
        assert(len(self._chain), len(self._v_mode))
        return len(self._chain)

    def __iter__(self):
        """Python 2.3 for i in x support
        """
        assert(len(self._chain), len(self._v_mode))
        return iter(zip(self._chain, self._v_mode))

    def __cmp__(self, key):
        if isinstance(key, ValidationChain):
            str = repr(key)
        else:
            str = key
        return cmp(repr(self), str)

    def __getitem__(self, idx):
        """self[idx] support and Python 2.1 for i in x support
        """
        assert(len(self._chain), len(self._v_mode))
        return self._chain[idx], self._v_mode[idx]

    def append(self, id_or_obj, mode=V_REQUIRED):
        """Appends a validator
        """
        validator = self.setValidator(id_or_obj)
        self.setMode(validator, mode)

    def appendRequired(self, id_or_obj):
        """Appends a validator as required
        """
        self.append(id_or_obj, mode=V_REQUIRED)

    def appendSufficient(self, id_or_obj):
        """Appends a validator as sufficient
        """
        self.append(id_or_obj, mode=V_SUFFICIENT)

    def insert(self, id_or_obj, mode=V_REQUIRED, position=0):
        """Inserts a validator at position (default 0)
        """
        validator = self.setValidator(id_or_obj, position=position)
        self.setMode(validator, mode, position=position)

    def insertRequired(self, id_or_obj, position=0):
        """Inserts a validator as required at position (default 0)
        """
        self.insert(id_or_obj, mode=V_REQUIRED, position=0)

    def insertSufficient(self, id_or_obj, position=0):
        """Inserts a validator as required at position (default 0)
        """
        self.insert(id_or_obj, mode=V_SUFFICIENT, position=0)

    def setMode(self, validator, mode, position=None):
        """Set mode
        """
        assert(mode in (V_REQUIRED, V_SUFFICIENT))
        # validator not required
        if position is None:
            self._v_mode.append(mode)
        else:
            self._v_mode.insert(position, mode)
        assert(len(self._chain), len(self._v_mode))

    def setValidator(self, id_or_obj, position=None):
        """Set validator
        """
        validator = validationService.validatorFor(id_or_obj)

        if position is None:
            self._chain.append(validator)
        else:
            self._chain.insert(position, validator)

        return validator

    def __call__(self, value, *args, **kwargs):
        """Do validation
        """
        results = {}
        failed = False
        for validator, mode in self:
            name = validator.name
            result = validator(value, *args, **kwargs)
            if result == True:
                if mode == V_SUFFICIENT:
                    return True # validation was successful
                elif mode == V_REQUIRED:
                    continue    # go on
                else:
                    raise ValidatorError, 'Unknown mode %s' % mode
            else:
                if mode == V_SUFFICIENT:
                    if type(result) in StringTypes:
                        # don't log if validator doesn't return an error msg
                        results[name] = result
                    continue # no fatal error, go on
                elif mode == V_REQUIRED:
                    if type(result) in StringTypes:
                        # don't log if validator doesn't return an error msg
                        results[name] = result
                    failed = True
                    break    # fatal error, stop and fail
                else:
                    raise ValidatorError, 'Unknown mode %s' % mode

        if failed:
            return '\n'.join([
                              #'%s: %s' % (name, res)
                              '%s' % res
                              for name, res in results.items()]
                            )
        else:
            return True


def test():
    """Little test script
    """
    isEmptyURL = ValidationChain('isEmptyURL',
                                validators = (('isEmpty', V_SUFFICIENT), ('isURL', V_REQUIRED)),
                                register=True
                               )
    #
    v = validationService.validatorFor('isEmptyURL')
    assert(v is isEmptyURL)
    assert(v('http://www.example.org') is True)
    assert(v('') is True)
    assert(type(v('www.example.org')) is StringType) # error

    isIntOrEmpty = ValidationChain('isIntOrEmpty')
    isIntOrEmpty.appendSufficient('isEmpty')
    from Products.Archetypes.validation.implementation import RegexValidator
    isPosInt = RegexValidator('isInt', r'^([+])?\d+$', title='', description='')
    isIntOrEmpty.appendRequired(isPosInt)
    validationService.register(isIntOrEmpty)

    v = validationService.validatorFor('isIntOrEmpty')
    assert(v is isIntOrEmpty)
    assert(v('') is True)
    assert(v('1') is True)
    assert(type(v('-1')) is StringType) # error
    assert(type(v('a')) is StringType) # error

test()

if __name__ == '__main__':
    test()
