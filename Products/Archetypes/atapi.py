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
"""
"""
# registering and type processing
from Products.Archetypes.lib.register import registerType
from Products.Archetypes.lib.register import process_types
from Products.Archetypes.lib.register import listTypes
from Products.Archetypes.lib.register import registerClasses
# base classes
from Products.Archetypes.bases.baseobject import BaseObject
from Products.Archetypes.bases.basecontent import BaseContent
from Products.Archetypes.bases.basecontent import BaseContentMixin
from Products.Archetypes.bases.basefolder import BaseFolder
from Products.Archetypes.bases.basefolder import BaseFolderMixin
from Products.Archetypes.bases.basetool import BaseTool
from Products.Archetypes.bases.basetool import BaseFolderishTool
from Products.Archetypes.bases.basebtreefolder import BaseBTreeFolder
from Products.Archetypes.bases.baseorderedfolder import OrderedBaseFolder
from Products.Archetypes.bases.extensiblemetadata import ExtensibleMetadata
from Products.Archetypes.bases.templatemixin import TemplateMixin
# base class schemata instances
from Products.Archetypes.bases.baseobject import MinimalSchema
from Products.Archetypes.bases.basecontent import BaseSchema
from Products.Archetypes.bases.basefolder import BaseFolderSchema
from Products.Archetypes.bases.basebtreefolder import BaseBTreeFolderSchema
from Products.Archetypes.bases.extensiblemetadata import ExtensibleMetadataSchema
from Products.Archetypes.bases.baseorderedfolder import OrderedBaseFolderSchema
# schemata classes
from Products.Archetypes.schemata import *
#from Products.Archetypes.schemata import BasicSchema
#from Products.Archetypes.schemata import Schema
#from Products.Archetypes.schemata import MetadataSchema
#from Products.Archetypes.schemata import ManagedSchema
#from Products.Archetypes.schemata import CompositeSchema
#from Products.Archetypes.schemata import FacadeMetadataSchema
#from Products.Archetypes.schemata import VariableSchemaSupport
# marshaller
from Products.Archetypes.marshallers import PrimaryFieldMarshaller
from Products.Archetypes.marshallers import RFC822Marshaller
# fields
from Products.Archetypes.fields import *
# widgets
from Products.Archetypes.widgets import *
# storage
from Products.Archetypes.storages import *
#from Products.Archetypes.storage.AggregatedStorage import AggregatedStorage
#from Products.Archetypes.storage.SQLStorage import BaseSQLStorage
#from Products.Archetypes.storage.SQLStorage import GadflySQLStorage
#from Products.Archetypes.storage.SQLStorage import MySQLSQLStorage
#from Products.Archetypes.storage.SQLStorage import PostgreSQLStorage
#from Products.Archetypes.storage.SQLStorage import SQLServerStorage
# misc
from Products.Archetypes.lib.vocabulary import DisplayList
from Products.Archetypes.lib.vocabulary import Vocabulary
from Products.Archetypes.lib.classgen import AT_GENERATE_METHOD
from Products.Archetypes.lib.baseunit import BaseUnit
from Products.Archetypes.lib.logging import log
from Products.Archetypes.lib.logging import log_exc

# dynamicly calculate which modules should be exported
import sys
skipExports = ('skipExports', 'sys',)
__all__ = tuple([ export
                  for export in dir(sys.modules[__name__])
                  if export not in skipExports and not export.startswith('_')
                ])
