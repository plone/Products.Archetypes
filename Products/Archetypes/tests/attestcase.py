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

# the output of some tests may differ when CMFPlone is installed
try:
    import Products.CMFPlone
except ImportError:
    HAS_PLONE = HAS_PLONE21 = False
else:
    HAS_PLONE = True
    try:
        from Products.CMFPlone.migrations import v2_1
    except ImportError:
        HAS_PLONE21 = False
    else:
        HAS_PLONE21 = True

# Use either plain CMF or Plone to run the portal tests
# You have to install:
#  * CMF, CMFQuickInstaller, CMFFormController, CMFTestCase for CMF tests
#  * Plone and PloneTestCase for Plone tests
#USE_PLONETESTCASE = True
#USE_PLONETESTCASE = False
USE_PLONETESTCASE = HAS_PLONE

print "Using Plone TestCase", USE_PLONETESTCASE, HAS_PLONE, HAS_PLONE21

if not USE_PLONETESTCASE:
    # setup is installing some required products
    import Products.CMFTestCase.setup
    # install the rest manually
    ZopeTestCase.installProduct('CMFCalendar')
    ZopeTestCase.installProduct('CMFTopic')
    ZopeTestCase.installProduct('DCWorkflow')
    ZopeTestCase.installProduct('CMFActionIcons')
    ZopeTestCase.installProduct('CMFQuickInstallerTool')
    ZopeTestCase.installProduct('CMFFormController')
    ZopeTestCase.installProduct('ZCTextIndex')
    ZopeTestCase.installProduct('PageTemplates', quiet=1)
    ZopeTestCase.installProduct('PythonScripts', quiet=1)
    ZopeTestCase.installProduct('ExternalMethod', quiet=1)
else:
    # setup is installing all required products
    import Products.PloneTestCase.setup

DEPS_AT = ('MimetypesRegistry', 'PortalTransforms', 'Archetypes',
            'ArchetypesTestUpdateSchema',)

# install products
for product in DEPS_AT:
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

from Testing.ZopeTestCase import user_name
from Testing.ZopeTestCase import user_password
default_user = user_name
default_role = 'Member'


__all__ = ('USE_PLONETESTCASE', 'HAS_PLONE',
           'default_user', 'default_role', 'user_name', 'user_password',
           'ATTestCase', 'ATFunctionalTestCase', )
