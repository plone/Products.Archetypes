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
"""Registry package
"""

# public methods
from Products.Archetypes.registry.base import registerComponent
from Products.Archetypes.registry.base import registerRegistry
from Products.Archetypes.registry.base import getRegistry
from Products.Archetypes.registry.property import registerProperty

# registries
#from Products.Archetypes.registry.attype import typeRegistry
#from Products.Archetypes.registry.field import fieldRegistry
#from Products.Archetypes.registry.property import propertyRegistry
#from Products.Archetypes.registry.storage import storageRegistry
#from Products.Archetypes.registry.validator import validatorRegistry
#from Products.Archetypes.registry.widget import widgetRegistry

import Products.Archetypes.registry.attype
import Products.Archetypes.registry.field
import Products.Archetypes.registry.property
import Products.Archetypes.registry.storage
import Products.Archetypes.registry.validator
import Products.Archetypes.registry.widget

__all__ = ('registerComponent', 'registerRegistry', 'getRegistry', 'registerProperty')
