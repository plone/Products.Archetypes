from AccessControl import ClassSecurityInfo
from DateTime.DateTime import DateTime
from Field import MetadataField, LinesField, DateTimeField, \
     MetadataFieldList, IntegerField, ObjectField
from Widget import StringWidget, TextAreaWidget, BooleanWidget, KeywordWidget, SelectionWidget, \
     LinesWidget, CalendarWidget
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.utils  import getToolByName
from Products.CMFDefault.DublinCore import DefaultDublinCoreImpl
from types import StringType

from debug import log, log_exc
import Persistence

from utils import DisplayList

## MIXIN
class ExtensibleMetadata(DefaultDublinCoreImpl, Persistence.Persistent):
    security = ClassSecurityInfo()
    security.declareObjectPublic()
    security.setDefaultAccess('allow')
    
    schema = type = MetadataFieldList((
        ObjectField('allowDiscussion',
                      accessor="isDiscussable",
                      mutator="allowDiscussion",
                      default=None,
                      enforceVocabulary=1,
                      vocabulary=DisplayList(((0, 'Disabled'), (1, 'Enabled'),
                                              (None, 'Default'))),
                      widget=SelectionWidget(label="Allow Discussion?",
                                             label_msgid="label_allow_discussion",
                                             description_msgid="help_allow_discussion",
                                             i18n_domain="plone"),
                      ),
              
        LinesField('subject',
                   multiValued=1,
                   accessor="Subject",
                   widget=KeywordWidget(label="Keywords",
                                        label_msgid="label_keywords",
                                        description_msgid="help_keywords",
                                        i18n_domain="plone"),
                   ),
        
        MetadataField('description',
                      default='',
                      searchable=1,
                      accessor="Description",
                      widget=TextAreaWidget(description="An administrative summary of the content",
                                            label_msgid="label_description",
                                            description_msgid="help_description",
                                            i18n_domain="plone"), 
                      ),

        LinesField('contributors',
                   accessor="Contributors",
                   widget=LinesWidget(label_msgid="label_contributors",
                                      description_msgid="help_contributors",
                                      i18n_domain="plone"),
                   ),
        
        DateTimeField('effectiveDate',
                      accessor="EffectiveDate",
                      widget=CalendarWidget(label="Effective Date",
                                            description="""Date when the
                      content should become availble on the public
                      site""",
                                            label_msgid="label_effective_date",
                                            description_msgid="help_effective_date",
                                            i18n_domain="plone")),
        
        DateTimeField('expirationDate',
                      accessor="ExpirationDate",
                      widget=CalendarWidget(label="Expiration Date",
                                            description="""Date when the
                      content should no longer be visible on the
                      public site""",
                                            label_msgid="label_expiration_date",
                                            description_msgid="help_expiration_date",
                                            i18n_domain="plone")),
        
        MetadataField('language',
                      accessor="Language",
                      default="en",
                      vocabulary='languages',
                      widget=SelectionWidget(label_msgid="label_language",
                                             description_msgid="help_language",
                                             i18n_domain="plone"),
                      ),
        
        MetadataField('rights',
                      accessor="Rights",
                      widget=TextAreaWidget(description="A list of copyright info for this content",
                                            label_msgid="label_copyrights",
                                            description_msgid="help_copyrights",
                                            i18n_domain="plone")),
        
     ))

    def isDiscussable(self):
        result = None
        try:
            result = getToolByName(self, 'portal_discussion').isDiscussionAllowedFor(self)
        except:
            pass
        return result
    
    def allowDiscussion(self, allowDiscussion=None):
        if allowDiscussion is not None:
            try:
                allowDiscussion = int(allowDiscussion)
            except:
                if type(allowDiscussion) == StringType:
                    allowDiscussion = allowDiscussion.lower().strip()
                    allowDiscussion = {'on' : 1, 'off': 0, 'none':None}.get(allowDiscussion, None)

            try:
                getToolByName(self, 'portal_discussion').overrideDiscussionFor(self, allowDiscussion)
            except:
                log_exc()
                pass
            
    def setSubject(self, value):
        if type(value) == type(''):
            value =  value.split('\n')
            value = [v.strip() for v in value if v.strip()]
        value = filter(None, value)
        self.subject = value
    
    ##Vocab Methods
    def languages(self):
        available_langs = getattr(self, 'availableLanguages', None)
        if available_langs is None:
            return DisplayList((('en','English'), ('fr','French'), ('es','Spanish'), \
                                ('pt','Portuguese'), ('ru','Russian')))
        if callable(available_langs):
            available_langs = available_langs()
        return DisplayList(available_langs)


InitializeClass(ExtensibleMetadata)
