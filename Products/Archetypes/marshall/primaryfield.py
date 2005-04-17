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

from Globals import InitializeClass
from AccessControl import ClassSecurityInfo
from OFS.content_types import guess_content_type

from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.marshall.base import Marshaller

class PrimaryFieldMarshaller(Marshaller):

    security = ClassSecurityInfo()
    security.declareObjectPrivate()
    security.setDefaultAccess('deny')

    def demarshall(self, instance, data, **kwargs):
        p = instance.getPrimaryField()
        p.set(instance, data, **kwargs)

    def marshall(self, instance, **kwargs):
        p = instance.getPrimaryField()
        data = p and instance[p.getName()] or ''
        content_type = length = None
        # Gather/Guess content type
        if IBaseUnit.isImplementedBy(data):
            content_type = data.getContentType()
            length = data.get_size()
            data   = data.getRaw()
        else:
            log("WARNING: PrimaryFieldMarshaller(%r): field %r does not return a IBaseUnit instance." % (instance, p.getName()))
            if hasattr(p, 'getContentType'):
                content_type = p.getContentType(instance) or 'text/plain'
            else:
                content_type = data and guess_content_type(data) or 'text/plain'
            # XXX FIXME
            # DM 2004-12-01: "FileField"s represent a major field class
            #  that does not use "IBaseUnit" yet.
            #  Ensure, the used "File" objects get the correct length.
            if hasattr(p, 'get_size'):
                length = p.get_size(instance)
            else:
                # DM: this almost surely is stupid!
                length = len(data)

            # ObjectField without IBaseUnit?
            if shasattr(data, 'data'):
                data = data.data
            else:
                data = str(data)
                # DM 2004-12-01: recompute 'length' as we now know it definitely
                length = len(data)
        return (content_type, length, data)

InitializeClass(PrimaryFieldMarshaller)
