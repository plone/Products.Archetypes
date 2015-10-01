# -*- coding: utf-8 -*-
from Products.Archetypes import atapi
from Products.Archetypes import Field
from SimpleType import SimpleType
from Products.Archetypes.config import PKG_NAME
from zope.i18nmessageid import MessageFactory


fields = ['StringField',
          'FileField', 'TextField', 'DateTimeField', 'LinesField',
          'IntegerField', 'FloatField', 'FixedPointField',
          'BooleanField', 'ImageField'
          ]

field_instances = []

for f in fields:
    field_instances.append(getattr(Field, f)(f.lower()))

schema = atapi.Schema(tuple(field_instances) + (
    atapi.LinesField('selectionlinesfield1',
                     vocabulary='_get_selection_vocab',
                     enforceVocabulary=1,
                     widget=atapi.SelectionWidget(label='Selection'),
                     ),
    atapi.LinesField('selectionlinesfield2',
                     vocabulary='_get_selection_vocab',
                     widget=atapi.SelectionWidget(
                         label='Selection', i18n_domain="attesti18n"),
                     ),
    atapi.LinesField('selectionlinesfield3',
                     vocabulary='_get_selection_vocab2',
                     widget=atapi.MultiSelectionWidget(
                         label='MultiSelection', i18n_domain="attesti18n"),
                     ),
    atapi.TextField('textarea_appendonly',
                    widget=atapi.TextAreaWidget(label='TextArea',
                                                append_only=1,),
                    ),
    atapi.TextField('textarea_appendonly_timestamp',
                    widget=atapi.TextAreaWidget(label='TextArea',
                                                append_only=1,
                                                timestamp=1,),
                    ),
    atapi.TextField('textarea_maxlength',
                    widget=atapi.TextAreaWidget(label='TextArea',
                                                maxlength=20,),
                    ),
    atapi.TextField('richtextfield',
                    allowable_content_types=('text/plain',
                                             'text/structured',
                                             'text/restructured',
                                             'text/html',
                                             'application/msword'),
                    widget=atapi.RichWidget(label='rich'),
                    ),
    atapi.ReferenceField('referencefield',
                         relationship='complextype',
                         widget=atapi.ReferenceWidget(addable=1),
                         allowed_types=('ComplexType', ),
                         multiValued=1,
                         ),
)) + atapi.ExtensibleMetadata.schema


_domain1 = MessageFactory('domain1')
_domain2 = MessageFactory('domain2')


class ComplexType(SimpleType):
    """A simple archetype"""
    schema = SimpleType.schema + schema
    archetype_name = meta_type = "ComplexType"
    portal_type = 'ComplexType'

    def _get_selection_vocab(self):
        return atapi.DisplayList((
            ('foo', u'Foo'),
            ('complex', u'C\xf6mpl\xe8x'),
            ('bar', _domain1(u'Bar')),
            ('hello', _domain2(u'Hello')),
        ))

    def _get_selection_vocab2(self):
        return atapi.DisplayList((
            ('foo2', u'Foo 2'),
            ('complex2', u'C\xf6mpl\xe8x 2'),
            ('bar2', _domain1(u'Bar 2')),
            ('hello2', _domain2(u'Hello 2')),
        ))


atapi.registerType(ComplexType, PKG_NAME)
