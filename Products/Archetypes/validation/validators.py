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

from Products.Archetypes.validation.implementation import RangeValidator
from Products.Archetypes.validation.implementation import RegexValidator
from Products.Archetypes.validation.implementation import EmptyValidator
from Products.Archetypes.validation.implementation import MaxSizeValidator
from Products.Archetypes.validation.implementation import DateValidator
from Products.Archetypes.validation.implementation import TALValidator
from Products.Archetypes.validation.service import validationService as vs

vs.register(RangeValidator('inNumericRange', title='', description=''))
vs.register(RegexValidator('isDecimal',
                   r'^([+-]?)(?=\d|\.\d)\d*(\.\d*)?([Ee]([+-]?\d+))?$',
                   title='', description='',
                   errmsg='is not a decimal number.'))
vs.register(RegexValidator('isInt', r'^([+-])?\d+$', title='', description='',
                   errmsg='is not an integer.'))
vs.register(RegexValidator('isPrintable', r'[a-zA-Z0-9\s]+$', title='', description='',
                   errmsg='contains unprintable characters'))
vs.register(RegexValidator('isSSN', r'^\d{9}$', title='', description='',
                   errmsg='is not a well formed SSN.'))
vs.register(RegexValidator('isUSPhoneNumber', r'^\d{10}$', ignore='[\(\)\-\s]',
                   title='', description='',
                   errmsg='is not a valid us phone number.'))
vs.register(RegexValidator('isInternationalPhoneNumber', r'^\d+$', ignore='[\(\)\-\s\+]',
                   title='', description='',
                   errmsg='is not a valid international phone number.'))
vs.register(RegexValidator('isZipCode', r'^(\d{5}|\d{9})$',
                   title='', description='',
                   errmsg='is not a valid zip code.'))
vs.register(RegexValidator('isURL', r'(ht|f)tps?://[^\s\r\n]+',
                   title='', description='',
                   errmsg='is not a valid url (http, https or ftp).'))
vs.register(RegexValidator('isEmail', "^([0-9a-zA-Z_&.+-]+!)*[0-9a-zA-Z_&.+-]+@(([0-9a-z]([0-9a-z-]*[0-9a-z])?\.)+[a-z]{2,6}|([0-9]{1,3}\.){3}[0-9]{1,3})$",
                   title='', description='',
                   errmsg='is not a valid email address.'))
vs.register(RegexValidator('isUnixLikeName', '^[A-Za-z][\w\d\-\_]{0,7}',
                   title="", description="",
                   errmsg="this name is not a valid identifier"))
vs.register(MaxSizeValidator('isMaxSize', title='', description=''))
vs.register(DateValidator('isValidDate', title='', description=''))
vs.register(EmptyValidator('isEmpty', title='', description=''))
vs.register(EmptyValidator('isEmptyNoError', title='', description='',
                   showError=False))
vs.register(TALValidator('isTAL', title='', description=''))

