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
__author__ = "Christian Heimes"

from Testing import ZopeTestCase
from Testing.ZopeTestCase.functional import Functional

DEPS = ('CMFCore', 'CMFDefault', 'CMFCalendar', 'CMFTopic',
        'DCWorkflow', 'CMFActionIcons', 'CMFQuickInstallerTool',
        'CMFFormController',  'ZCTextIndex', 'TextIndexNG2',
        'MailHost', 'PageTemplates', 'PythonScripts', 'ExternalMethod',
        )
DEPS_PLONE = ('GroupUserFolder', 'SecureMailHost', 'CMFPlone',)
DEPS_OWN = ('MimetypesRegistry', 'PortalTransforms', 'Archetypes',
            'ArchetypesTestUpdateSchema',)

default_user = ZopeTestCase.user_name
default_role = 'Member'

# install products
for product in DEPS + DEPS_OWN:
    ZopeTestCase.installProduct(product)

# Fixup zope 2.7+ configuration
try:
    from App import config
except ImportError:
    pass
else:
    config._config.rest_input_encoding = 'ascii'
    config._config.rest_output_encoding = 'ascii'
    config._config.rest_header_level = 3
    del config

class ATTestCase(ZopeTestCase.ZopeTestCase):
    """Simple AT test case
    """

class ATFunctionalTestCase(Functional, ATTestCase):
    """Simple AT test case for functional tests
    """
    __implements__ = Functional.__implements__ + ATTestCase.__implements__ 
    
__all__ = ('default_user', 'default_role', 'ATTestCase',
           'ATFunctionalTestCase', )
