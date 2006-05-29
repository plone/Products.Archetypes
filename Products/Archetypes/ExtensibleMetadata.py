from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from Field import *
from Widget import *
from Schema import MetadataSchema
from DateTime.DateTime import DateTime
from Globals import InitializeClass, DTMLFile
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.utils  import getToolByName
from interfaces.metadata import IExtensibleMetadata
from debug import log, log_exc
import Persistence

from utils import DisplayList

from Products.CMFDefault.utils import _dtmldir
_marker=[]

FLOOR_DATE = DateTime( 1000, 0 ) # always effective
CEILING_DATE = DateTime( 9999, 0 ) # never expires

## MIXIN
class ExtensibleMetadata(Persistence.Persistent):
    """a replacement for CMFDefault.DublinCore.DefaultDublinCoreImpl
    """


    # XXX This is not completely true. We need to review this later
    # and make sure it is true.
    # Just so you know, the problem here is that Title
    # is on BaseObject.schema, so it does implement IExtensibleMetadata
    # as long as both are used together.
    __implements__ = IExtensibleMetadata

    security = ClassSecurityInfo()

    schema = type = MetadataSchema(
        (
        StringField(
            'allowDiscussion',
            accessor="isDiscussable",
            mutator="allowDiscussion",
            default=None,
            enforceVocabulary=1,
            vocabulary=DisplayList(((0,'Disabled'),(1,'Enabled'),
                                   (None,'Default'))),
            widget=SelectionWidget(
                label="Allow Discussion?",
                label_msgid="label_allow_discussion",
                description_msgid="help_allow_discussion",
                i18n_domain="plone"),
        ),
        LinesField(
            'subject',
            multiValued=1,
            accessor="Subject",
            widget=KeywordWidget(
                label="Keywords",
                label_msgid="label_keywords",
                description_msgid="help_keywords",
                i18n_domain="plone"),
        ),
        TextField(
            'description',
            default='',
            searchable=1,
            accessor="Description",
            widget=TextAreaWidget(
                label='Description',
                description="An administrative summary of the content",
                label_msgid="label_description",
                description_msgid="help_description",
                i18n_domain="plone"),
        ),
        LinesField(
            'contributors',
            accessor="Contributors",
            widget=LinesWidget(
                label='Contributors',
                label_msgid="label_contributors",
                description_msgid="help_contributors",
                i18n_domain="plone"),
        ),
        DateTimeField(
            'effectiveDate',
            mutator = 'setEffectiveDate',
            widget=CalendarWidget(
                label="Effective Date",
                description=("Date when the content should become available "
                             "on the public site"),
                label_msgid="label_effective_date",
                description_msgid="help_effective_date",
                i18n_domain="plone"),
        ),
        DateTimeField(
            'expirationDate',
            mutator = 'setExpirationDate',
            widget=CalendarWidget(
                label="Expiration Date",
                description=("Date when the content should no longer be "
                             "visible on the public site"),
                label_msgid="label_expiration_date",
                description_msgid="help_expiration_date",
                i18n_domain="plone"),
        ),

        StringField(
            'language',
            accessor="Language",
            default="en",
            vocabulary='languages',
            widget=SelectionWidget(
                label='Language',
                label_msgid="label_language",
                description_msgid="help_language",
                i18n_domain="plone"),
        ),
        StringField(
            'rights',
            accessor="Rights",
            widget=TextAreaWidget(
                label='Copyright',
                description="A list of copyright info for this content",
                label_msgid="label_copyrights",
                description_msgid="help_copyrights",
                i18n_domain="plone")),
        ))

    def __init__(self):
        now = DateTime()
        self.creation_date = now
        self.modification_date = now

    security.declareProtected(CMFCorePermissions.View,
                              'isDiscussable')
    def isDiscussable(self, encoding=None):
        dtool = getToolByName(self, 'portal_discussion')
        return dtool.isDiscussionAllowedFor(self)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'allowDiscussion')
    def allowDiscussion(self, allowDiscussion=None, **kw):
        if allowDiscussion is not None:
            try:
                allowDiscussion = int(allowDiscussion)
            except (TypeError, ValueError):
                allowDiscussion = allowDiscussion.lower().strip()
                d = {'on' : 1, 'off': 0, 'none':None, '':None}
                allowDiscussion = d.get(allowDiscussion, None)
        dtool = getToolByName(self, 'portal_discussion')
        dtool.overrideDiscussionFor(self, allowDiscussion)

    # Vocabulary methods ######################################################

    security.declareProtected(CMFCorePermissions.View,
                              'languages')
    def languages(self):
        available_langs = getattr(self, 'availableLanguages', None)
        if available_langs is None:
            return DisplayList(
                (('en','English'), ('fr','French'), ('es','Spanish'),
                 ('pt','Portuguese'), ('ru','Russian')))
        if callable(available_langs):
            available_langs = available_langs()
        return DisplayList(available_langs)


    #  DublinCore interface query methods #####################################

    security.declareProtected(CMFCorePermissions.View,
                              'CreationDate')
    def CreationDate(self):
        """ Dublin Core element - date resource created.
        """
        # return unknown if never set properly
        return self.creation_date and self.creation_date.ISO() or 'Unknown'

    security.declarePublic( CMFCorePermissions.View,
                            'EffectiveDate')
    def EffectiveDate(self):
        """ Dublin Core element - date resource becomes effective.
        """
        ed = self.schema['effectiveDate'].get(self)
        return ed and ed.ISO() or 'None'

    security.declarePublic( CMFCorePermissions.View,
                            'ExpirationDate')
    def ExpirationDate(self):
        """
            Dublin Core element - date resource expires.
        """
        ed = self.schema['expirationDate'].get(self)
        return ed and ed.ISO() or 'None'

    security.declareProtected(CMFCorePermissions.View,
                              'Date')
    def Date(self):
        """
        Dublin Core element - default date
        """
        # Return effective_date if specifically set, modification date
        # otherwise
        date = self.schema['effectiveDate'].get(self)
        if date is None:
            date = self.modified()
        return date.ISO()

    security.declareProtected(CMFCorePermissions.View,
                              'Format')
    def Format(self):
        """cmf/backward compat
        Dublin Core element - resource format
        """
        # FIXME: get content type from marshaller
        return

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'setFormat')
    def setFormat(self, value):
        """cmf/backward compat: ignore setFormat"""
        pass

    #  DublinCore utility methods #############################################

    security.declareProtected(CMFCorePermissions.View,
                              'contentEffective')
    def contentEffective(self, date):
        """ Is the date within the resource's effective range? """
        effectiveDate = self.schema['effectiveDate'].get(self)
        expirationDate = self.schema['expirationDate'].get(self)
        pastEffective = ( effectiveDate is None
                       or effectiveDate <= date )
        beforeExpiration = ( expirationDate is None
                          or expirationDate >= date )
        return pastEffective and beforeExpiration

    security.declareProtected(CMFCorePermissions.View,
                              'contentExpired')
    def contentExpired(self, date=None):
        """ Is the date after resource's expiration """
        if not date:
            # XXX we need some unittesting for this
            date = DateTime()
        expirationDate = self.schema['expirationDate'].get(self)
        if not expirationDate:
            expirationDate = CEILING_DATE
        return expirationDate <= date

    #  CatalogableDublinCore methods ##########################################

    security.declareProtected(CMFCorePermissions.View,
                              'created')
    def created(self):
        """Dublin Core element - date resource created,
        returned as DateTime.
        """
        # allow for non-existent creation_date, existed always
        date = getattr( self, 'creation_date', None )
        return date is None and self.FLOOR_DATE or date

    security.declareProtected(CMFCorePermissions.View,
                              'modified')
    def modified(self):
        """Dublin Core element - date resource last modified,
        returned as DateTime.
        """
        return self.modification_date

    security.declareProtected(CMFCorePermissions.View,
                              'effective')
    def effective(self):
        """Dublin Core element - date resource becomes effective,
        returned as DateTime.
        """
        effective = self.schema['effectiveDate'].get(self)
        if effective is None:
            return FLOOR_DATE
        return effective

    security.declareProtected(CMFCorePermissions.View,
                              'expires')
    def expires(self):
        """Dublin Core element - date resource expires,
        returned as DateTime.
        """
        expires = self.schema['expirationDate'].get(self)
        if expires is None:
            return CEILING_DATE
        return expires

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

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'notifyModified')
    def notifyModified(self):
        """
        Take appropriate action after the resource has been modified.
        For now, change the modification_date.
        """
        # XXX This could also store the id of the user doing modifications.
        self.setModificationDate()

    # XXX Could this be simply protected by ModifyPortalContent ?
    security.declarePrivate('setModificationDate')
    def setModificationDate(self, modification_date=None):
        """Set the date when the resource was last modified.
        When called without an argument, sets the date to now.
        """
        if not modification_date:
            self.modification_date = DateTime()
        else:
            if not isinstance( modification_date, DateTime ):
                modification_date = DateTime( modification_date )
            self.modification_date = self._datify(modification_date)

    security.declarePrivate( '_datify' )
    def _datify(self, attrib):
        if attrib == 'None':
            attrib = None
        elif not isinstance(attrib, DateTime):
            if attrib is not None:
                attrib = DateTime(attrib)
        return attrib

    #
    #  DublinCore interface query methods
    #

    security.declareProtected(CMFCorePermissions.View,
                              'Creator')
    def Creator(self):
        # XXX: fixme using 'portal_membership' -- should iterate over
        #       *all* owners
        "Dublin Core element - resource creator"
        owner = self.getOwner()
        if hasattr( owner, 'getUserName' ):
            return owner.getUserName()
        return 'No owner'

    security.declareProtected(CMFCorePermissions.View,
                              'Publisher')
    def Publisher(self):
        """Dublin Core element - resource publisher"""
        # XXX: fixme using 'portal_metadata'
        return 'No publisher'

    security.declareProtected(CMFCorePermissions.View,
                              'ModificationDate')
    def ModificationDate(self):
        """ Dublin Core element - date resource last modified.
        """
        return self.modified().ISO()

    security.declareProtected(CMFCorePermissions.View,
                              'Type')
    def Type(self):
        """Dublin Core element - Object type"""
        if hasattr(aq_base(self), 'getTypeInfo'):
            ti = self.getTypeInfo()
            if ti is not None:
                return ti.Title()
        return self.meta_type

    security.declareProtected(CMFCorePermissions.View,
                              'Identifier')
    def Identifier(self):
        """Dublin Core element - Object ID"""
        # XXX: fixme using 'portal_metadata' (we need to prepend the
        #      right prefix to self.getPhysicalPath().
        return self.absolute_url()

    #
    #  DublinCore utility methods
    #

    security.declareProtected(CMFCorePermissions.View,
                              'content_type')
    def content_type(self):
        """ WebDAV needs this to do the Right Thing (TM).
        """
        return self.Format()
    #
    #  CatalogableDublinCore methods
    #

    security.declareProtected(CMFCorePermissions.View,
                              'getMetadataHeaders')
    def getMetadataHeaders(self):
        """ Return RFC-822-style headers.
        """
        hdrlist = []
        hdrlist.append( ( 'Title', self.Title() ) )
        hdrlist.append( ( 'Subject', string.join( self.Subject(), ', ' ) ) )
        hdrlist.append( ( 'Publisher', self.Publisher() ) )
        hdrlist.append( ( 'Description', self.Description() ) )
        hdrlist.append( ( 'Contributors', string.join(
            self.Contributors(), '; ' ) ) )
        hdrlist.append( ( 'Effective_date', self.EffectiveDate() ) )
        hdrlist.append( ( 'Expiration_date', self.ExpirationDate() ) )
        hdrlist.append( ( 'Type', self.Type() ) )
        hdrlist.append( ( 'Format', self.Format() ) )
        hdrlist.append( ( 'Language', self.Language() ) )
        hdrlist.append( ( 'Rights', self.Rights() ) )
        return hdrlist

    #
    #  Management tab methods
    #

    security.declarePrivate( '_editMetadata' )
    def _editMetadata(self
                      , title=_marker
                      , subject=_marker
                      , description=_marker
                      , contributors=_marker
                      , effective_date=_marker
                      , expiration_date=_marker
                      , format=_marker
                      , language=_marker
                      , rights=_marker
                      ):
        """ Update the editable metadata for this resource.
        """
        if title is not _marker:
            self.setTitle( title )
        if subject is not _marker:
            self.setSubject( subject )
        if description is not _marker:
            self.setDescription( description )
        if contributors is not _marker:
            self.setContributors( contributors )
        if effective_date is not _marker:
            self.setEffectiveDate( effective_date )
        if expiration_date is not _marker:
            self.setExpirationDate( expiration_date )
        if format is not _marker:
            self.setFormat( format )
        if language is not _marker:
            self.setLanguage( language )
        if rights is not _marker:
            self.setRights( rights )

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'manage_metadata' )
    manage_metadata = DTMLFile('zmi_metadata', _dtmldir)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                               'manage_editMetadata')
    def manage_editMetadata( self
                           , title
                           , subject
                           , description
                           , contributors
                           , effective_date
                           , expiration_date
                           , format
                           , language
                           , rights
                           , REQUEST
                           ):
        """ Update metadata from the ZMI.
        """
        self._editMetadata( title, subject, description, contributors
                          , effective_date, expiration_date
                          , format, language, rights
                          )
        REQUEST[ 'RESPONSE' ].redirect( self.absolute_url()
                                + '/manage_metadata'
                                + '?manage_tabs_message=Metadata+updated.' )

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'editMetadata')
    def editMetadata(self
                     , title=''
                     , subject=()
                     , description=''
                     , contributors=()
                     , effective_date=None
                     , expiration_date=None
                     , format='text/html'
                     , language='en-US'
                     , rights=''
                     ):
        """
        used to be:  editMetadata = WorkflowAction(_editMetadata)
        Need to add check for webDAV locked resource for TTW methods.
        """
        self.failIfLocked()
        self._editMetadata(title=title
                           , subject=subject
                           , description=description
                           , contributors=contributors
                           , effective_date=effective_date
                           , expiration_date=expiration_date
                           , format=format
                           , language=language
                           , rights=rights
                           )
        self.reindexObject()


InitializeClass(ExtensibleMetadata)
