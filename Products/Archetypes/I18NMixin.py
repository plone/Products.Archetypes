from Schema import Schema
from Field import I18NStringField, I18NTextField
from Widget import TextAreaWidget, StringWidget
from Storage import MetadataStorage
from Products.CMFCore import CMFCorePermissions

i18n_schema = Schema((
    I18NStringField('title',
                    required=1,
                    searchable=1,
                    default='',
                    accessor='Title',
                    widget=StringWidget(label_msgid="label_title",
                                        description_msgid="help_title",
                                        i18n_domain="plone"),
                    ),
    I18NTextField('description',
                  searchable=1,
                  default_output_type='text/html',
                  allowable_content_types=('text/restructured',
                                           'text/plain',
                                           'text/html'),
                  isMetadata=1,
                  storage=MetadataStorage(),
                  schemata='metadata',
                  widget=TextAreaWidget(description="An administrative summary of the content",
                                        label_msgid="label_description",
                                        description_msgid="help_description",
                                        i18n_domain="plone"),
                  )
    ))


class I18NMixin:
    """ handle I18N title and description, plus I18N related actions
    """
    schema = i18n_schema

    actions = ({ 'id': 'translate',
                 'name': 'Translate',
                 'action': 'portal_form/base_translation',
                 'permissions': (CMFCorePermissions.ModifyPortalContent,),
                 },
               { 'id': 'translations',
                 'name': 'Translations',
                 'action': 'portal_form/manage_translations_form',
                 'permissions': (CMFCorePermissions.ModifyPortalContent,),
                 },
               )
    def setDescription(self, text, mimetype=None, lang=None):
        descr_field = self.Schema()['description']
        if text or descr_field.getRaw(self):
            # FIXME: pb if we try to call set before the object was added
            # (try to access to the mimetypes tool)
            descr_field.set(self, text, mimetype=mimetype, lang=lang)
        
    def Description(self):
        descr_field = self.Schema()['description']
        return descr_field.get(self)
    
    def setTitle(self, text, mimetype=None, lang=None):
        title_field = self.Schema()['title']
        if text or title_field.getRaw(self):
            # FIXME: pb if we try to call set before the object was added
            # (try to access to the mimetypes tool)
            title_field.set(self, text, lang=lang)
        
    def Title(self):
        title_field = self.Schema()['title']
        return title_field.get(self)

