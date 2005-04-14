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

from Interface import Interface
from Interface import Attribute

class IValidationService(Interface):

    def validate(name_or_validator, value, *args, **kwargs):
        """call the validator of a given name"""

    def validatorFor(name_or_validator):
        """return the validator for a given name"""

    def register(validator):
        """load a validator for access by name"""

    def unregister(name_or_validator):
        """unregisters a validator by name"""

class IValidator(Interface):

    name = Attribute("name of the validator")
    title = Attribute("title or name of the validator")
    description = Attribute("description of the validator")

    def __call__(value, *args, **kwargs):
        """return True if valid, error string if not"""


class IValidationChain(IValidator):
    """Marker interface for a chain
    """
