from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from ExtensionClass import Base
from Products.CMFCore  import CMFCorePermissions
from Schema import Schema
from Field import I18NStringField, I18NTextField, ComputedField
from Widget import TextAreaWidget, StringWidget
from Storage import MetadataStorage
from BaseObject import BaseObject
from ZODB.PersistentMapping import PersistentMapping

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
                  ),
    ComputedField('language',
                  searchable=0,
                  isMetadata=1,
                  accessor='Language',
                  expression='context.getContentLanguage()',
                  widget=StringWidget(label="Language")
                  ),
    ))


class I18NMixin(Base):
    """ I18NMixin for content objects

    handle :
      _ methods specific to objects with I18N content
      _ I18N title and description
      _ I18N related actions
    """
    schema = i18n_schema
    actions = ({ 'id': 'translate',
                 'name': 'Translate',
                 'action': 'base_translation',
                 'permissions': (CMFCorePermissions.ModifyPortalContent,),
                 },
               { 'id': 'translations',
                 'name': 'Translations',
                 'action': 'manage_translations_form',
                 'permissions': (CMFCorePermissions.ModifyPortalContent,),
                 },
               )

    security = ClassSecurityInfo()

    _need_redirect = 0


    def __init__(self):
        self._translations_states = PersistentMapping()
        
##     security.declarePrivate('manage_afterAdd')
##     def manage_afterAdd(self, item, container):
##         # we need to delete title property so we can still use property sheet from the ZMI
##         try:
##             aq_base(self).manage_delProperties(('title',))
##         except KeyError:
##             pass
        
    # we need to override some Dublin Core methods to make them works cleanly i18nized
    
    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'setDescription')
    def setDescription(self, text, mimetype=None, encoding=None, lang=None):
        "Dublin Core element - resource summary"
        descr_field = self.Schema()['description']
        if text or descr_field.getRaw(self):
            # FIXME: pb if we try to call set before the object was added
            # (try to access to the mimetypes tool)
            descr_field.set(self, text, mimetype=mimetype, encoding=encoding, lang=lang)
        
    security.declarePublic('Description')
    def Description(self, lang=None):
        "Dublin Core element - resource summary"
        descr_field = self.Schema()['description']
        return descr_field.get(self, lang)
    
    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'setTitle')
    def setTitle(self, text, encoding=None, lang=None):
        "Dublin Core element - resource name"
        title_field = self.Schema()['title']
        if text or title_field.getRaw(self):
            # FIXME: pb if we try to call set before the object was added
            # (try to access to the mimetypes tool)
            title_field.set(self, text, encoding=encoding, lang=lang)
        
    security.declarePublic('Title')
    def Title(self, lang=None):
        "Dublin Core element - resource name"
        title_field = self.Schema()['title']
        return title_field.get(self, lang)

    def setLanguage(self, language, encoding=None):
        "Dublin Core element - resource language"
        pass
    
    # i18n content management method ##########################################
    
    security.declarePublic('getFilteredLanguages')
    def getFilteredLanguages(self, REQUEST=None):
        """return a list of all existant languages for this instance
        each language is a tuple (id, label)
        """
        langs = {}
        for field in self.Schema().values():
            if field.hasI18NContent():
                for lang in field.getDefinedLanguages(self):
                    langs[lang] = 1
        result = []
        for lang_id in langs.keys():
            try:
                result.append((lang_id, self.languageDescription(lang_id)))
            except KeyError:
                continue
        return result

    security.declarePublic('getMasterLanguage')
    def getMasterLanguage(self):
        """return the id for the master language"""
        if getattr(self, '_master_language', None) is not None:
            return self._master_language
        try:
            sp = self.portal_properties.site_properties
            return sp.getProperty('default_language', 'en')
        except AttributeError:
            return 'en'

    security.declarePublic('getTranslationState')
    def getTranslationState(self, lang=None):
        """return the string describing the translation state"""
        lang = self.getContentLanguage(lang)
        try:
            return self._translations_states[lang]
        except:
            if lang == self.getMasterLanguage():
                return "master translation"
            return ''

    security.declareProtected(CMFCorePermissions.ModifyPortalContent, 'manage_translations')
    def manage_translations(self, REQUEST=None, **kwargs):
        """delete given translations or set the master translation"""
        if not kwargs:
            kwargs = REQUEST.form
        if kwargs.has_key('setmaster'):
            del kwargs['setmaster']
            if len(kwargs) != 1:
                raise Exception('You must select one language to set it as the master translation')
            lang = kwargs.keys()[0]
            # check this is a valid language id
            self.languageDescription(lang)    
            self._master_language = lang
        else:
            if kwargs.has_key(self.getMasterLanguage()):
                raise Exception('You can not delete the master translation')
            for lang_id in kwargs.keys():
                for field in self.Schema().values():
                    if field.hasI18NContent():
                        field.unset(self, lang=lang_id)

    # path / url redirection methods ##########################################
    
    security.declarePublic('needLanguageRedirection')
    def needLanguageRedirection(self):
        """notify that the language as changed, so a redirection is needed to
        make the correct language appears in the url
        """
        self._need_redirect = 1
        
    def __before_publishing_traverse__(self, other, REQUEST):
        # prevent further traversal
        if self._need_redirect:
            stack = REQUEST['TraversalRequestNameStack']
            try:
                self.languageDescription(stack[-1])
                # this is a language, delete it from the stack and redirect to
                # the current language
                del stack[-1]
                self._need_redirect = 0
                stack.reverse()
                REQUEST.RESPONSE.redirect(self.absolute_url() + '/' + '/'.join(stack))
            except:
                pass

    def __bobo_traverse__(self, REQUEST, name):
        """
        allow access to different translations of the object by adding the lang
        code to its url
        """
        # FIXME: beurk        
        target = BaseObject.__bobo_traverse__(self, REQUEST, name)
        if target is not None:
            return target
        # FIXME : backward compat
        if not hasattr(self, '_need_redirect'):
            self._need_redirect = 0
        # is it a given translation
        try:
            self.languageDescription(name)
            if not self._need_redirect:
                self.setCurrentLanguage(name, redirect=0)
            return self
        except:
            # this is not a valid language id
            if hasattr(REQUEST, 'RESPONSE'):
                REQUEST.RESPONSE.notFoundError("%s\n%s" % (name, ''))
            else:
                raise AttributeError(name)

    def _processForm(self, data=1, metadata=None):
        # FIXME: beurk        
        BaseObject._processForm(self, data, metadata)
        form = self.REQUEST.form
        base_lang = self.getContentLanguage()
        if self.hasI18NContent():
            # set other translations as outdated if we are currently processing
            # the main translation
            m_lang = self.getMasterLanguage()
            if base_lang == m_lang:
                for lang_desc in self.getFilteredLanguages():
                    if lang_desc[0] != m_lang:
                        old_value = self._translations_states.get(lang_desc[0], '')
                        if old_value.find('outdated') == -1:
                            self._translations_states[lang_desc[0]] = old_value + ' (outdated)'

            # else try to get and set the translation state
            elif form.has_key('_translation_state'):
                self._translations_states[base_lang] = form['_translation_state']
        
