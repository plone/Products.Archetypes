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

from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.lib.logging import log
from Products.Archetypes.lib.utils import shasattr

from Acquisition import aq_base
from Globals import PersistentMapping

from AccessControl import ClassSecurityInfo
from Products.Archetypes.storages.base import Storage
from Products.Archetypes.storages.base import StorageLayer
from Products.Archetypes.storages.base import type_map
from Products.Archetypes.storages.storage import ReadOnlyStorage
from Products.Archetypes.storages.storage import AttributeStorage
from Products.Archetypes.storages.storage import ObjectManagedStorage
from Products.Archetypes.storages.storage import MetadataStorage
from Products.Archetypes.storages.annotation import AnnotationStorage
from Products.Archetypes.storages.annotation import MetadataAnnotationStorage
from Products.Archetypes.storages.aggregated import AggregatedStorage
from Products.Archetypes.storages.facade import FacadeMetadataStorage
from Products.Archetypes.storages.sql.storage import BaseSQLStorage
from Products.Archetypes.storages.sql.storage import GadflySQLStorage
from Products.Archetypes.storages.sql.storage import MySQLSQLStorage
from Products.Archetypes.storages.sql.storage import PostgreSQLStorage
from Products.Archetypes.storages.sql.storage import SQLServerStorage


__all__ = ('Storage', 'StorageLayer', 'ReadOnlyStorage', 'ObjectManagedStorage',
           'MetadataStorage', 'AttributeStorage', 'AnnotationStorage',
           'MetadataAnnotationStorage', 'AggregatedStorage',
           'FacadeMetadataStorage', 'BaseSQLStorage', 'GadflySQLStorage',
           'PostgreSQLStorage', 'SQLServerStorage',
          )
