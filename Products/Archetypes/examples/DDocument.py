from Products.Archetypes import atapi
from Products.Archetypes.TemplateMixin import TemplateMixin
from Products.Archetypes.Marshall import PrimaryFieldMarshaller
from Products.Archetypes.config import PKG_NAME

schema = atapi.BaseSchema + atapi.Schema((
    atapi.TextField('teaser',
                    searchable=1,
                    widget=atapi.TextAreaWidget(description="""A short lead-in to the
              article so that we might get people to read the body""",
                                                label="Teaser",
                                                rows=3)),

    # Using a bare ObjetField doesn't make sense ...
    # ObjectField('author'),
    atapi.StringField('author'),

    atapi.TextField('body',
                    required=1,
                    primary=1,
                    searchable=1,
                    default_output_type='text/html',
                    allowable_content_types=('text/restructured',
                                             'text/plain',
                                             'text/html',
                                             'application/msword'),
                    widget=atapi.RichWidget(),
                    ),

    atapi.IntegerField("number",
                       index="FieldIndex",
                       default=42,
                       validators=('isInt',),
                       ),

    atapi.ImageField('image',
                     default_output_type='image/jpeg',
                     allowable_content_types=('image/*',),
                     widget=atapi.ImageWidget()),

    atapi.ReferenceField('related',
                         relationship='related',
                         multiValued=True,
                         widget=atapi.ReferenceWidget(),
                         keepReferencesOnCopy=True),

    atapi.ReferenceField('rel2',
                         relationship='rel2',
                         multiValued=True,
                         widget=atapi.ReferenceWidget(),
                         keepReferencesOnCopy=True),
),

    marshall=PrimaryFieldMarshaller()) + TemplateMixin.schema


class DDocument(TemplateMixin, atapi.BaseContent):
    """An extensible Document (test) type"""
    schema = schema
    archetype_name = "Demo Doc"
    actions = TemplateMixin.actions

    def manage_afterPUT(self, data, marshall_data, file, context, mimetype,
                        filename, REQUEST, RESPONSE):
        """For unit tests
        """
        self.called_afterPUT_hook = True


atapi.registerType(DDocument, PKG_NAME)
