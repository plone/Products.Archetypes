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

from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes import field as at_fields
from Products.Archetypes.example.simpletype import SimpleType

field_names = ['StringField',
          'FileField', 'TextField', 'DateTimeField', 'LinesField',
          'IntegerField', 'FloatField', 'FixedPointField',
          'BooleanField', 'ImageField'
          # 'ComputedField', 'CMFObjectField', 'ReferenceField'
          ]

field_instances = []

for f in field_names:
    field_instances.append(getattr(at_fields, f)(f.lower()))

schema = Schema(tuple(field_instances) + (
    LinesField('selectionlinesfield1',
               vocabulary='_get_selection_vocab',
               enforceVocabulary=1,
               widget=SelectionWidget(label='Selection'),
               ),
    LinesField('selectionlinesfield2',
               vocabulary='_get_selection_vocab',
               widget=SelectionWidget(label='Selection'),
               ),
    LinesField('selectionlinesfield3',
               vocabulary='_get_selection_vocab2',
               widget=MultiSelectionWidget(label='MultiSelection'),
               ),
    TextField('textarea_appendonly',
              widget=TextAreaWidget( label='TextArea',
                                     append_only=1,),
              ),
    TextField('richtextfield',
              allowable_content_types=('text/plain',
                                       'text/structured',
                                       'text/restructured',
                                       'text/html',
                                       'application/msword'),
              widget=RichWidget(label='rich'),
              ),
    ReferenceField('referencefield',
                   relationship='complextype',
                   widget=ReferenceWidget(addable=1),
                   allowed_types=('ComplexType', ),
                   multiValued=1,
                  ),
    #ReferenceField('reffield1',
    #               relationship='myref1',
    #               widget=InAndOutWidget(label='Ref1')
    #              ),
    #ReferenceField('reffield2',
    #               relationship='myref2',
    #               widget=PicklistWidget(label='Ref1'),
    #              ),
    )) + ExtensibleMetadata.schema

class ComplexType(SimpleType):
    """A simple archetype"""
    schema = SimpleType.schema + schema
    archetype_name = meta_type = "Complex Type"
    portal_type = 'ComplexType'

    def _get_selection_vocab(self):
        return DisplayList((('Test','Test'), ))

    def _get_selection_vocab2(self):
        return DisplayList((('Test','Test'),('Test2','Test2'), ))


registerType(ComplexType, PKG_NAME)
