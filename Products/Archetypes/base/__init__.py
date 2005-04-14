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

# base classes
from Products.Archetypes.base.baseobject import BaseObject
from Products.Archetypes.base.basecontent import BaseContent
from Products.Archetypes.base.basecontent import BaseContentMixin
from Products.Archetypes.base.basefolder import BaseFolder
from Products.Archetypes.base.basefolder import BaseFolderMixin
from Products.Archetypes.base.basetool import BaseTool
from Products.Archetypes.base.basetool import BaseFolderishTool
from Products.Archetypes.base.basebtreefolder import BaseBTreeFolder
from Products.Archetypes.base.baseorderedfolder import OrderedBaseFolder
from Products.Archetypes.base.extensiblemetadata import ExtensibleMetadata
from Products.Archetypes.base.templatemixin import TemplateMixin
# base class schemata instances
from Products.Archetypes.base.baseobject import MinimalSchema
from Products.Archetypes.base.basecontent import BaseSchema
from Products.Archetypes.base.basefolder import BaseFolderSchema
from Products.Archetypes.base.basebtreefolder import BaseBTreeFolderSchema
from Products.Archetypes.base.extensiblemetadata import ExtensibleMetadataSchema
from Products.Archetypes.base.baseorderedfolder import OrderedBaseFolderSchema
