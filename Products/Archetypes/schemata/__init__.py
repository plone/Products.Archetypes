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

from Products.Archetypes.schemata.composity import CompositeSchema
from Products.Archetypes.schemata.facade import FacadeMetadataSchema
from Products.Archetypes.schemata.schema import BasicSchema
from Products.Archetypes.schemata.schema import Schema
from Products.Archetypes.schemata.schema import WrappedSchema
from Products.Archetypes.schemata.schema import ManagedSchema
from Products.Archetypes.schemata.schema import MetadataSchema
from Products.Archetypes.schemata.schemata import getNames
from Products.Archetypes.schemata.schemata import getSchemata
from Products.Archetypes.schemata.schemata import Schemata
from Products.Archetypes.schemata.schemata import WrappedSchemata
from Products.Archetypes.schemata.schemata import SchemaLayerContainer
from Products.Archetypes.schemata.variable import VariableSchemaSupport

FieldList = Schema
MetadataFieldList = MetadataSchema

__all__ = ('CompositeSchema', 'FacadeMetadataSchema', 'BasicSchema', 'Schema',
    'WrappedSchema', 'ManagedSchema', 'MetadataSchema', 'getNames',
    'getSchemata', 'Schemata', 'WrappedSchemata', 'SchemaLayerContainer',
    'VariableSchemaSupport',
    )

