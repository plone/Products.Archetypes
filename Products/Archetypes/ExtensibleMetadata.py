import string
from logging import DEBUG
from zope.component import queryUtility
from zope.interface import implementer

from Products.Archetypes import PloneMessageFactory as _
from Products.Archetypes.Field import BooleanField, LinesField, TextField, \
    StringField, DateTimeField
from Products.Archetypes.Widget import (
    BooleanWidget, TagsWidget, TextAreaWidget, StringWidget,
    DatetimeWidget, SelectWidget, AjaxSelectWidget)
from Products.Archetypes.Schema import Schema
from Products.Archetypes.Schema import MetadataSchema
from Products.Archetypes.interfaces import IExtensibleMetadata
from Products.Archetypes.log import log
from Products.Archetypes.utils import DisplayList, shasattr
from Products.Archetypes import config
import Persistence
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from DateTime.DateTime import DateTime
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from Products.CMFCore import permissions
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.log import log_deprecated
from ComputedAttribute import ComputedAttribute

_marker = []

# http://www.zope.org/Collectors/CMF/325
# http://www.zope.org/Collectors/CMF/476
_zone = DateTime().timezone()

FLOOR_DATE = DateTime(1000, 1)  # always effective
CEILING_DATE = DateTime(2500, 0)  # never expires

# We import this conditionally, in order not to introduce a hard dependency
try:
    from plone.i18n.locales.interfaces import IMetadataLanguageAvailability
    HAS_PLONE_I18N = True
except ImportError:
    HAS_PLONE_I18N = False


# MIXIN
@implementer(IExtensibleMetadata)
class ExtensibleMetadata(Persistence.Persistent):
    """ A DC metadata implementation for Plone Archetypes
    """

    security = ClassSecurityInfo()

    schema = type = MetadataSchema((
        BooleanField(
            'allowDiscussion',
            accessor="isDiscussable",
            mutator="allowDiscussion",
            edit_accessor="editIsDiscussable",
            default=None,
            enforceVocabulary=1,
            widget=BooleanWidget(
                label=_(u'label_allow_comments',
                        default=u'Allow comments'),
                description=_(u'help_allow_comments',
                              default=u'If selected, users can add comments '
                              'to this item.')
            ),
        ),
        LinesField(
            'subject',
            multiValued=1,
            accessor="Subject",
            searchable=True,
            widget=TagsWidget(
                label=_(u'label_tags', default=u'Tags'),
                description=_(u'help_tags',
                              default=u'Tags are commonly used for ad-hoc '
                              'organization of content.'),
            ),
        ),
        TextField(
            'description',
            default='',
            searchable=1,
            accessor="Description",
            default_content_type='text/plain',
            widget=TextAreaWidget(
                label=_(u'label_description', default=u'Description'),
                description=_(u'help_description',
                              default=u'Used in item listings and search results.'),
            ),
        ),
        # Location, also known as Coverage in the DC metadata standard, but we
        # keep the term Location here for historical reasons.
        StringField(
            'location',
            # why no accessor? http://dev.plone.org/plone/ticket/6424
            searchable=True,
            widget=StringWidget(
                label=_(u'label_location', default=u'Location'),
                description=_(u'help_location_dc',
                              default=u'The geographical location associated with the item, if applicable.'),
            ),
        ),
        LinesField(
            'contributors',
            accessor="Contributors",
            widget=AjaxSelectWidget(
                label=_(u'label_contributors', u'Contributors'),
                description=_(u'help_contributors',
                              default=u"The names of people that have contributed "
                              "to this item. Each contributor should "
                              "be on a separate line."),
                vocabulary="plone.app.vocabularies.Users"
            ),
        ),
        LinesField(
            'creators',
            accessor="Creators",
            widget=AjaxSelectWidget(
                label=_(u'label_creators', u'Creators'),
                description=_(u'help_creators',
                              default=u"Persons responsible for creating the content of "
                              "this item. Please enter a list of user names, one "
                              "per line. The principal creator should come first."),
                vocabulary="plone.app.vocabularies.Users"
            ),
        ),
        DateTimeField(
            'effectiveDate',
            mutator='setEffectiveDate',
            languageIndependent=True,
            widget=DatetimeWidget(
                label=_(u'label_effective_date', u'Publishing Date'),
                description=_(u'help_effective_date',
                              default=u"The date when the item will be published. If no "
                              "date is selected the item will be published immediately."),
            ),
        ),
        DateTimeField(
            'expirationDate',
            mutator='setExpirationDate',
            languageIndependent=True,
            widget=DatetimeWidget(
                label=_(u'label_expiration_date', u'Expiration Date'),
                description=_(u'help_expiration_date',
                              default=u"The date when the item expires. This will automatically "
                              "make the item invisible for others at the given date. "
                              "If no date is chosen, it will never expire."),
            ),
        ),
        StringField(
            'language',
            accessor="Language",
            default=config.LANGUAGE_DEFAULT,
            default_method='defaultLanguage',
            vocabulary='languages',
            widget=SelectWidget(
                label=_(u'label_language', default=u'Language'),
            ),
        ),
        TextField(
            'rights',
            accessor="Rights",
            default_method='defaultRights',
            allowable_content_types=('text/plain',),
            widget=TextAreaWidget(
                label=_(u'label_copyrights', default=u'Rights'),
                description=_(u'help_copyrights',
                              default=u'Copyright statement or other rights information on this item.'),
            )),
    )) + Schema((
        # XXX change this to MetadataSchema in AT 1.4
        # Currently we want to stay backward compatible without migration
        # between beta versions so creation and modification date are using the
        # standard schema which leads to AttributeStorage
        DateTimeField(
                'creation_date',
                accessor='created',
                mutator='setCreationDate',
                default_method=DateTime,
                languageIndependent=True,
                isMetadata=True,
                schemata='metadata',
                generateMode='mVc',
                widget=DatetimeWidget(
                    label=_(u'label_creation_date', default=u'Creation Date'),
                    description=_(u'help_creation_date',
                                  default=u'Date this object was created'),
                    visible={'edit': 'invisible', 'view': 'invisible'}),
                ),
        DateTimeField(
            'modification_date',
            accessor='modified',
            mutator='setModificationDate',
            default_method=DateTime,
            languageIndependent=True,
            isMetadata=True,
            schemata='metadata',
            generateMode='mVc',
            widget=DatetimeWidget(
                    label=_(u'label_modification_date',
                            default=u'Modification Date'),
                    description=_(u'help_modification_date',
                                  default=u'Date this content was modified last'),
                    visible={'edit': 'invisible', 'view': 'invisible'}),
        ),
    ))

    def __init__(self):
        pass

    security.declarePrivate('defaultLanguage')

    def defaultLanguage(self):
        # Retrieve the default language
        tool = getToolByName(self, 'portal_languages', None)
        if tool is not None:
            return tool.getDefaultLanguage()
        return config.LANGUAGE_DEFAULT

    security.declarePrivate('defaultRights')

    def defaultRights(self):
        # Retrieve the default rights.
        mdtool = getToolByName(self, 'portal_metadata', None)
        if mdtool is None:
            return ''
        for sid, schema in mdtool.listSchemas():
            if not hasattr(schema, 'listPolicies'):
                # Broken class from CMFDefault.
                continue
            for pid, policy in schema.listPolicies(typ=self.Type()):
                if pid != 'Rights' and not policy.supply_default:
                    continue
                return policy.default_value
        return ''

    security.declareProtected(permissions.View, 'isDiscussable')

    def isDiscussable(self, encoding=None):
        log_deprecated(
            "The isDiscussable method from the ExtensibleMetadata in "
            "Products.ATContentTypes has been deprecated and will be removed "
            "in Plone 5. This method belongs to the old discussion "
            "infrastructure that already has been replaced by "
            "plone.app.discussion in Plone 4.1."
        )
        if not 'portal_discussion' in self.objectIds():
            return
        # Returns either True or False
        dtool = getToolByName(self, 'portal_discussion')
        return dtool.isDiscussionAllowedFor(self)

    security.declareProtected(permissions.View, 'editIsDiscussable')

    def editIsDiscussable(self, encoding=None):
        log_deprecated(
            "The editIsDiscussable method from the ExtensibleMetadata in "
            "Products.ATContentTypes has been deprecated and will be removed "
            "in Plone 5. This method belongs to the old discussion "
            "infrastructure that already has been replaced by "
            "plone.app.discussion in Plone 4.1."
        )
        if not 'portal_discussion' in self.objectIds():
            return
        # Returns True, False or if None the default value
        result = self.rawIsDiscussable()
        if result is not None:
            return result
        default = self.defaultIsDiscussable()
        return default

    security.declareProtected(permissions.View, 'rawIsDiscussable')

    def rawIsDiscussable(self):
        log_deprecated(
            "The rawIsDiscussable method from the ExtensibleMetadata in "
            "Products.ATContentTypes has been deprecated and will be removed "
            "in Plone 5. This method belongs to the old discussion "
            "infrastructure that already has been replaced by "
            "plone.app.discussion in Plone 4.1."
        )
        if not 'portal_discussion' in self.objectIds():
            return
        # Returns True, False or None where None means use the default
        result = getattr(aq_base(self), 'allow_discussion', None)
        if result is not None:
            result = bool(result)
        return result

    security.declareProtected(permissions.View, 'defaultIsDiscussable')

    def defaultIsDiscussable(self):
        log_deprecated(
            "The defaultIsDiscussable method from the ExtensibleMetadata in "
            "Products.ATContentTypes has been deprecated and will be removed "
            "in Plone 5. This method belongs to the old discussion "
            "infrastructure that already has been replaced by "
            "plone.app.discussion in Plone 4.1."
        )
        if not 'portal_discussion' in self.objectIds():
            return
        # Returns the default value, either True or False
        default = None
        typeInfo = self.getTypeInfo()
        if typeInfo:
            default = typeInfo.allowDiscussion()
        return default

    security.declareProtected(permissions.ModifyPortalContent,
                              'allowDiscussion')

    def allowDiscussion(self, allowDiscussion=None, **kw):
        pass

    # Vocabulary methods ######################################################

    security.declareProtected(permissions.View, 'languages')

    def languages(self):
        # Vocabulary method for the language field.
        util = None

        use_combined = False
        # Respect the combined language code setting from PloneLanguageTool
        lt = getToolByName(self, 'portal_languages', None)
        if lt is not None:
            use_combined = lt.use_combined_language_codes

        # Try the utility first
        if HAS_PLONE_I18N:
            util = queryUtility(IMetadataLanguageAvailability)
        # Fall back to acquiring availableLanguages
        if util is None:
            languages = getattr(self, 'availableLanguages', None)
            if callable(languages):
                languages = languages()
            # Fall back to static definition
            if languages is None:
                return DisplayList(
                    (('en', 'English'), ('fr', 'French'), ('es', 'Spanish'),
                     ('pt', 'Portuguese'), ('ru', 'Russian')))
        else:
            languages = util.getLanguageListing(combined=use_combined)
            languages.sort(key=lambda x: x[1])
            # Put language neutral at the top.
            languages.insert(0, (u'', _(u'Language neutral')))
        return DisplayList(languages)

    #  DublinCore interface query methods #####################################

    security.declareProtected(permissions.View, 'CreationDate')

    def CreationDate(self, zone=None):
        # Dublin Core element - date resource created.
        if zone is None:
            zone = _zone
        creation = self.getField('creation_date').get(self)
        # return unknown if never set properly
        return creation is None and 'Unknown' or creation.toZone(zone).ISO8601()

    security.declareProtected(permissions.View, 'EffectiveDate')

    def EffectiveDate(self, zone=None):
        # Dublin Core element - date resource becomes effective.
        if zone is None:
            zone = _zone
        effective = self.getField('effectiveDate').get(self)
        return effective is None and 'None' or effective.toZone(zone).ISO8601()

    def _effective_date(self):
        # Computed attribute accessor.
        return self.getField('effectiveDate').get(self)

    security.declareProtected(permissions.View, 'effective_date')
    effective_date = ComputedAttribute(_effective_date, 1)

    security.declareProtected(permissions.View, 'ExpirationDate')

    def ExpirationDate(self, zone=None):
        # Dublin Core element - date resource expires.
        if zone is None:
            zone = _zone
        expires = self.getField('expirationDate').get(self)
        return expires is None and 'None' or expires.toZone(zone).ISO8601()

    def _expiration_date(self):
        # Computed attribute accessor.
        return self.getField('expirationDate').get(self)

    security.declareProtected(permissions.View, 'expiration_date')
    expiration_date = ComputedAttribute(_expiration_date, 1)

    security.declareProtected(permissions.View, 'Date')

    def Date(self, zone=None):
        # Dublin Core element - default date
        # Return effective_date if specifically set, modification date
        # otherwise
        if zone is None:
            zone = _zone
        effective = self.getField('effectiveDate').get(self)
        if effective is None:
            effective = self.modified()
        return (effective is None and DateTime().toZone(zone) or
                effective.toZone(zone).ISO8601())

    security.declareProtected(permissions.View, 'Format')

    def Format(self):
        # cmf/backward compat
        # Dublin Core element - resource format
        # FIXME: get content type from marshaller
        return self.getContentType()

    security.declareProtected(permissions.ModifyPortalContent,
                              'setFormat')

    def setFormat(self, value):
        # cmf/backward compat: ignore setFormat.
        self.setContentType(value)

    def Identifer(self):
        # dublin core getId method.
        return self.getId()

    #  DublinCore utility methods #############################################

    security.declareProtected(permissions.View, 'contentEffective')

    def contentEffective(self, date):
        # Is the date within the resource's effective range?
        effective = self.getField('effectiveDate').get(self)
        expires = self.getField('expirationDate').get(self)
        pastEffective = (effective is None or effective <= date)
        beforeExpiration = (expires is None or expires >= date)
        return pastEffective and beforeExpiration

    security.declareProtected(permissions.View, 'contentExpired')

    def contentExpired(self, date=None):
        # Is the date after resource's expiration.
        if not date:
            date = DateTime()
        expires = self.getField('expirationDate').get(self)
        if not expires:
            expires = CEILING_DATE
        return expires <= date

    #  CatalogableDublinCore methods ##########################################

    security.declareProtected(permissions.View, 'created')

    def created(self):
        # Dublin Core element - date resource created,
        # returned as DateTime.
        # allow for non-existent creation_date, existed always
        created = self.getField('creation_date').get(self)
        return created is None and FLOOR_DATE or created

    security.declareProtected(permissions.View, 'modified')

    def modified(self):
        # Dublin Core element - date resource last modified,
        # returned as DateTime.
        modified = self.getField('modification_date').get(self)
        # TODO may return None
        return modified

    security.declareProtected(permissions.View, 'effective')

    def effective(self):
        # Dublin Core element - date resource becomes effective,
        # returned as DateTime.
        effective = self.getField('effectiveDate').get(self)
        return effective is None and FLOOR_DATE or effective

    security.declareProtected(permissions.View, 'expires')

    def expires(self):
        # Dublin Core element - date resource expires,
        # returned as DateTime.
        expires = self.getField('expirationDate').get(self)
        return expires is None and CEILING_DATE or expires

    ## code below come from CMFDefault.DublinCore.DefaultDublinCoreImpl #######

    ###########################################################################
    #
    # Copyright (c) 2001 Zope Corporation and Contributors. All Rights Reserved
    #
    # This software is subject to the provisions of the Zope Public License,
    # Version 2.0 (ZPL).  A copy of the ZPL should accompany this distribution.
    # THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
    # WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
    # WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
    # FOR A PARTICULAR PURPOSE
    #
    ###########################################################################

    #
    #  Set-modification-date-related methods.
    #  In DefaultDublinCoreImpl for lack of a better place.
    #

    security.declareProtected(permissions.ModifyPortalContent,
                              'notifyModified')

    def notifyModified(self):
        # Take appropriate action after the resource has been modified.
        # For now, change the modification_date.
        self.setModificationDate(DateTime())
        if shasattr(self, 'http__refreshEtag'):
            self.http__refreshEtag()

    security.declareProtected(permissions.ManagePortal,
                              'setModificationDate')

    def setModificationDate(self, modification_date=None):
        # Set the date when the resource was last modified.
        # When called without an argument, sets the date to now.
        if modification_date is None:
            modified = DateTime()
        else:
            modified = self._datify(modification_date)
        self.getField('modification_date').set(self, modified)

    security.declareProtected(permissions.ManagePortal,
                              'setCreationDate')

    def setCreationDate(self, creation_date=None):
        # Set the date when the resource was created.
        # When called without an argument, sets the date to now.
        if creation_date is None:
            created = DateTime()
        else:
            created = self._datify(creation_date)
        self.getField('creation_date').set(self, created)

    security.declarePrivate('_datify')

    def _datify(self, date):
        # Try to convert something into a DateTime instance or None.
        # stupid web
        if date == 'None':
            date = None
        if not isinstance(date, DateTime):
            if date is not None:
                date = DateTime(date)
        return date

    #
    #  DublinCore interface query methods
    #
    security.declareProtected(permissions.View, 'Publisher')

    def Publisher(self):
        # Dublin Core element - resource publisher
        # XXX: fixme using 'portal_metadata'
        return 'No publisher'

    security.declareProtected(permissions.View, 'ModificationDate')

    def ModificationDate(self, zone=None):
        # Dublin Core element - date resource last modified.
        if zone is None:
            zone = _zone
        modified = self.modified()
        return (modified is None and DateTime().toZone(zone)
                or modified.toZone(zone).ISO8601())

    security.declareProtected(permissions.View, 'Type')

    def Type(self):
        # Dublin Core element - Object type.
        if hasattr(aq_base(self), 'getTypeInfo'):
            ti = self.getTypeInfo()
            if ti is not None:
                return ti.Title()
        return self.meta_type

    security.declareProtected(permissions.View, 'Identifier')

    def Identifier(self):
        # Dublin Core element - Object ID
        # XXX: fixme using 'portal_metadata' (we need to prepend the
        #      right prefix to self.getPhysicalPath().
        return self.absolute_url()

    security.declareProtected(permissions.View, 'listContributors')

    def listContributors(self):
        # Dublin Core element - Contributors.
        return self.Contributors()

    security.declareProtected(permissions.ModifyPortalContent,
                              'addCreator')

    def addCreator(self, creator=None):
        # Add creator to Dublin Core creators.
        if creator is None:
            mtool = getToolByName(self, 'portal_membership', None)
            if mtool is None:
                return
            creator = mtool.getAuthenticatedMember().getId()

        # call self.listCreators() to make sure self.creators exists
        curr_creators = self.listCreators()
        if creator and not creator in curr_creators:
            self.setCreators(curr_creators + (creator, ))

    security.declareProtected(permissions.View, 'listCreators')

    def listCreators(self):
        # List Dublin Core Creator elements - resource authors.
        creators = self.Schema()['creators']
        if not creators.get(self):
            # for content created with CMF versions before 1.5
            owner_tuple = self.getOwnerTuple()
            owner_id = owner_tuple and owner_tuple[1]
            if owner_id:
                creators.set(self, (owner_id,))
            else:
                creators.set(self, ())

        return creators.get(self)

    security.declareProtected(permissions.View, 'Creator')

    def Creator(self):
        # Dublin Core Creator element - resource author.
        creators = self.listCreators()
        return creators and creators[0] or ''

    #
    #  DublinCore utility methods
    #

    # Deliberately *not* protected by a security declaration
    # See https://dev.plone.org/archetypes/ticket/712
    def content_type(self):
        """ WebDAV needs this to do the Right Thing (TM).
        """
        return self.Format()
    #
    #  CatalogableDublinCore methods
    #

    security.declareProtected(permissions.View, 'getMetadataHeaders')

    def getMetadataHeaders(self):
        # Return RFC-822-style headers.
        hdrlist = []
        hdrlist.append(('Title', self.Title()))
        hdrlist.append(('Subject', string.join(self.Subject(), ', ')))
        hdrlist.append(('Publisher', self.Publisher()))
        hdrlist.append(('Description', self.Description()))
        hdrlist.append(('Contributors', string.join(
            self.Contributors(), '; ')))
        hdrlist.append(('Creators', string.join(
            self.Creators(), '; ')))
        hdrlist.append(('Effective_date', self.EffectiveDate()))
        hdrlist.append(('Expiration_date', self.ExpirationDate()))
        hdrlist.append(('Type', self.Type()))
        hdrlist.append(('Format', self.Format()))
        hdrlist.append(('Language', self.Language()))
        hdrlist.append(('Rights', self.Rights()))
        return hdrlist

    #
    #  Management tab methods
    #

    security.declarePrivate('_editMetadata')

    def _editMetadata(self,
                      title=_marker,
                      subject=_marker,
                      description=_marker,
                      contributors=_marker,
                      effective_date=_marker,
                      expiration_date=_marker,
                      format=_marker,
                      language=_marker,
                      rights=_marker,
                      ):
        # Update the editable metadata for this resource.
        if title is not _marker:
            self.setTitle(title)
        if subject is not _marker:
            self.setSubject(subject)
        if description is not _marker:
            self.setDescription(description)
        if contributors is not _marker:
            self.setContributors(contributors)
        if effective_date is not _marker:
            self.setEffectiveDate(effective_date)
        if expiration_date is not _marker:
            self.setExpirationDate(expiration_date)
        if format is not _marker:
            self.setFormat(format)
        if language is not _marker:
            self.setLanguage(language)
        if rights is not _marker:
            self.setRights(rights)

    security.declareProtected(permissions.ModifyPortalContent,
                              'manage_metadata')
    manage_metadata = DTMLFile('zmi_metadata', config._www)

    security.declareProtected(permissions.ModifyPortalContent,
                              'manage_editMetadata')

    def manage_editMetadata(self,
                            title,
                            subject,
                            description,
                            contributors,
                            effective_date,
                            expiration_date,
                            format,
                            language,
                            rights,
                            REQUEST,
                            ):
        """ Update metadata from the ZMI.
        """
        self._editMetadata(title, subject, description, contributors,
                           effective_date, expiration_date,
                           format, language, rights,
                           )
        REQUEST['RESPONSE'].redirect(self.absolute_url()
                                     + '/manage_metadata'
                                     + '?manage_tabs_message=Metadata+updated.')

    security.declareProtected(permissions.ModifyPortalContent,
                              'editMetadata')

    def editMetadata(self,
                     title='',
                     subject=(),
                     description='',
                     contributors=(),
                     effective_date=None,
                     expiration_date=None,
                     format='text/html',
                     language='en-US',
                     rights='',
                     ):
        # Used to be:  editMetadata = WorkflowAction(_editMetadata)
        # Need to add check for webDAV locked resource for TTW methods.
        self.failIfLocked()
        self._editMetadata(title=title,
                           subject=subject,
                           description=description,
                           contributors=contributors,
                           effective_date=effective_date,
                           expiration_date=expiration_date,
                           format=format,
                           language=language,
                           rights=rights,
                           )
        self.reindexObject()

InitializeClass(ExtensibleMetadata)

ExtensibleMetadataSchema = ExtensibleMetadata.schema

__all__ = ('ExtensibleMetadata', 'ExtensibleMetadataSchema', )
