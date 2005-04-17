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

class IStorage(Interface):
    """Abstraction around the storage of field level data"""

    def getName():
        """return the storage name"""

    def get(name, instance, **kwargs):
        """lookup a value for a given instance stored under 'name'"""

    def set(name, instance, value, **kwargs):
        """set a value under the key 'name' for retrevial by/for
        instance"""

    # XXX all implementions have no 'value' argument
    #def unset(name, instance, value, **kwargs):
    def unset(name, instance, **kwargs):
        """unset a value under the key 'name'.
        used when changing storage for a field."""

class ISQLStorage(IStorage):
    """ Marker interface for distinguishing ISQLStorages """
    pass
