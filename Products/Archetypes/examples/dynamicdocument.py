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

from Products.Archetypes.atapi import *

schema = BaseSchema + Schema((
    TextField('teaser',
              searchable=1,
              widget=TextAreaWidget(description="""A short lead-in to the
              article so that we might get people to read the body""",
                                    label="Teaser",
                                    rows=3)),

    # Using a bare ObjetField doesn't make sense ...
    #ObjectField('author'),
    StringField('author'),

    TextField('body',
              required=1,
              primary=1,
              searchable=1,
              default_output_type='text/html',
              allowable_content_types=('text/restructured',
                                       'text/plain',
                                       'text/html',
                                       'application/msword'),
              widget=RichWidget(),
              ),

    IntegerField("number",
                 index="FieldIndex",
                 default=42,
                 validators=('isInt',),
                 ),

    ImageField('image',
               default_output_type='image/jpeg',
               allowable_content_types=('image/*',),
               widget=ImageWidget()),

    ),
      marshall=PrimaryFieldMarshaller()) + TemplateMixin.schema

class DDocument(TemplateMixin, BaseContent):
    """An extensible Document (test) type"""
    schema = schema
    archetype_name = "Demo Doc"
    actions = TemplateMixin.actions


registerType(DDocument)

