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
from Products.PortalTransforms.libtransforms import utils as transform_utils

PKG_NAME = "Archetypes"
SKIN_NAME = "archetypes"
TOOL_NAME = "archetype_tool" ## Name the tool will be installed under

UID_CATALOG = "uid_catalog"

REGISTER_DEMO_TYPES = True ##Initialize the demo types
INSTALL_DEMO_TYPES = False ##Install the demo types
DEBUG = True  ## See debug messages

##Reference Engine bits
REFERENCE_CATALOG = "reference_catalog"
UUID_ATTR = "_at_uid"
REFERENCE_ANNOTATION = "at_references"

## In zope 2.6.3+ and 2.7.0b4+ a lines field returns a tuple not a list. Per
## default archetypes returns a tuple, too. If this breaks your software you
## can disable the change.
## See http://zope.org/Collectors/Zope/924
ZOPE_LINES_IS_TUPLE_TYPE = True

## MYSQL SQLStorage Table Type
## To use connections with ACID transactions you should define it as
## INNODB. The MySQL default table type is MyISAM.
MYSQL_SQLSTORAGE_TABLE_TYPE = 'INNODB'

## Debug security settings of Fields, Widgets and Storages?
DEBUG_SECURITY=False
#DEBUG_SECURITY=True

## If you have graphviz http://www.research.att.com/sw/tools/graphviz/
## and its frontend "dot" installed on your system set this to True
## You need dot version > 1.10 with cmapx support.
try:
    GRAPHVIZ_BINARY = transform_utils.bin_search('dot')
except transform_utils.MissingBinary:
    # graphviz not found
    GRAPHVIZ_BINARY = None
    HAS_GRAPHVIZ = False
else:
    HAS_GRAPHVIZ = True

## comment out the following line to enable the reference graph tool
HAS_GRAPHVIZ = False

## backward compatibility:
from types import StringTypes as STRING_TYPES

## detect Python Imaging Libraries
try:
    import PIL.Image
except ImportError:
    # no PIL, no scaled versions!
    log("Warning: no Python Imaging Libraries (PIL) found."+\
        "Archetypes based ImageField's don't scale if neccessary.")
    HAS_PIL=False
else:
    HAS_PIL=True

## set default marshaller
## if the Marshall product is available, use it!
try:
    from Products.Marshall import ControlledMarshaller
except:
    from marshallers import RFC822Marshaller
    DEFAULT_MARSHALLER = RFC822Marshaller
else:
    DEFAULT_MARSHALLER = ControlledMarshaller
