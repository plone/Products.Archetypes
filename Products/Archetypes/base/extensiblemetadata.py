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

from Products.Archetypes.field import *
from Products.Archetypes.widget import *
from Products.Archetypes.schema import Schema
from Products.Archetypes.schema import MetadataSchema
from Products.Archetypes.interfaces.metadata import IExtensibleMetadata
from Products.Archetypes.lib.vocabulary import DisplayList
from Products.Archetypes.lib.logging import log
from Products.Archetypes.lib.logging import log_exc
from Products.Archetypes.lib.logging import ERROR

import Persistence
from Acquisition import aq_base
from AccessControl import ClassSecurityInfo
from AccessControl import Unauthorized
from DateTime.DateTime import DateTime
from Globals import InitializeClass, DTMLFile
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.utils  import getToolByName
from Products.CMFDefault.utils import _dtmldir

_marker=[]

try:
    True
except NameError:
    True=1
    False=0

FLOOR_DATE = DateTime(1000, 0) # always effective
CEILING_DATE = DateTime(2500, 0) # never expires

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
            edit_accessor="editIsDiscussable",
            default=None,
            enforceVocabulary=1,
            vocabulary=DisplayList((
        ('None', 'Default', 'label_discussion_default'),
        ('1',    'Enabled', 'label_discussion_enabled'),
        ('0',    'Disabled', 'label_discussion_disabled'),
        )),
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
                description_msgid="help_keyword",
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
        LinesField(
            'creators',
            accessor="Creators",
            widget=LinesWidget(
                label='Creators',
                label_msgid="label_creators",
                description_msgid="help_creators",
                visible={'view':'hidden', 'edit':'hidden'},
                i18n_domain="plone"),
        ),
        DateTimeField(
            'effectiveDate',
            mutator='setEffectiveDate',
            languageIndependent = True,
            #default=FLOOR_DATE,
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
            mutator='setExpirationDate',
            languageIndependent = True,
            #default=CEILING_DATE,
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
            default=None,
            default_method="defaultLanguage",
            vocabulary='languages',
            widget=SelectionWidget(
                label='Language',
                label_msgid="label_language",
                description_msgid="help_language",
                i18n_domain="plone"),
        ),
        TextField(
            'rights',
            accessor="Rights",
            widget=TextAreaWidget(
                label='Copyright',
                description="A list of copyright info for this content",
                label_msgid="label_copyrights",
                description_msgid="help_copyrights",
                i18n_domain="plone")),
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
            widget=CalendarWidget(
                label="Creation Date",
                description=("Date this object was created"),
                label_msgid="label_creation_date",
                description_msgid="help_creation_date",
                i18n_domain="plone",
                visible={'edit':'invisible', 'view':'invisible'}),
        ),
        DateTimeField(
            'modification_date',
            accessor='modified',
            mutator = 'setModificationDate',
            default_method=DateTime,
            languageIndependent=True,
            isMetadata=True,
            schemata='metadata',
            generateMode='mVc',
            widget=CalendarWidget(
                label="Modification Date",
                description=("Date this content was modified last"),
                label_msgid="label_modification_date",
                description_msgid="help_modification_date",
                i18n_domain="plone",
                visible={'edit':'invisible', 'view':'invisible'}),
        ),
        ))

    def __init__(self):
        pass
        #self.setCreationDate(None)
        #self.setModificationDate(None)

    security.declarePrivate('defaultLanguage')
    def defaultLanguage(self):
        """ returns always None, keep method for subclassing purposes """
        return None

    security.declareProtected(CMFCorePermissions.View, 'isDiscussable')
    def isDiscussable(self, encoding=None):
        dtool = getToolByName(self, 'portal_discussion')
        return dtool.isDiscussionAllowedFor(self)

    security.declareProtected(CMFCorePermissions.View, 'editIsDiscussable')
    def editIsDiscussable(self, encoding=None):
        # XXX this method highly depends on the current implementation
        # it's a quick hacky fix
        result = getattr(aq_base(self), 'allow_discussion', None)
        return str(result)

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'allowDiscussion')
    def allowDiscussion(self, allowDiscussion=None, **kw):
        if allowDiscussion is not None:
            try:
                allowDiscussion = int(allowDiscussion)
            except (TypeError, ValueError):
                allowDiscussion = allowDiscussion.lower().strip()
                d = {'on' : 1, 'off': 0, 'none':None, '':None, 'None':None}
                allowDiscussion = d.get(allowDiscussion, None)
        dtool = getToolByName(self, 'portal_discussion')
        try:
            dtool.overrideDiscussionFor(self, allowDiscussion)
        except KeyError, err:
            if allowDiscussion is None:
                # work around a bug in CMFDefault.DiscussionTool. It's using
                # an unsafe hasattr() instead of a more secure getattr() on an
                # unwrapped object
                msg = "Unable to set discussion on %s to None. Already " \
                      "deleted allow_discussion attribute? Message: %s" % (
                       self.getPhysicalPath(), str(err))
                log(msg, level=ERROR)
            else:
                raise
        except ("Unauthorized", Unauthorized):
            # Catch Unauthorized exception that could be raised by the
            # discussion tool when the authenticated users hasn't
            # ModifyPortalContent permissions. IMO this behavior is safe because
            # this method is protected, too.
            # Explanation:
            # A user might have CreatePortalContent but not ModifyPortalContent
            # so allowDiscussion could raise a Unauthorized error although it's
            # called from trusted code. That is VERY bad inside setDefault()!
            #
            # XXX: Should we have our own implementation of
            #      overrideDiscussionFor?
            log_exc('Catched Unauthorized on disussiontool.' \
                    'overrideDiscussionFor(%s)' % self.absolute_url(1),
                    level=ERROR)

    # Vocabulary methods ######################################################

    security.declareProtected(CMFCorePermissions.View, 'languages')
    def languages(self):
        """Vocabulary method for the language field
        """
        # XXX document me
        # use a list of languages from PLT?
        available_langs = getattr(self, 'availableLanguages', None)
        if available_langs is None:
            return DisplayList(
                (('en','English'), ('fr','French'), ('es','Spanish'),
                 ('pt','Portuguese'), ('ru','Russian')))
        if callable(available_langs):
            available_langs = available_langs()
        return DisplayList(available_langs)


    #  DublinCore interface query methods #####################################

    security.declareProtected(CMFCorePermissions.View, 'CreationDate')
    def CreationDate(self):
        """ Dublin Core element - date resource created.
        """
        creation = self.getField('creation_date').get(self)
        # XXX return unknown if never set properly
        return creation is None and 'Unknown' or creation.ISO()

    security.declarePublic( CMFCorePermissions.View, 'EffectiveDate')
    def EffectiveDate(self):
        """ Dublin Core element - date resource becomes effective.
        """
        effective = self.getField('effectiveDate').get(self)
        # XXX None? FLOOR_DATE
        return effective is None and 'None' or effective.ISO()

    security.declarePublic( CMFCorePermissions.View, 'ExpirationDate')
    def ExpirationDate(self):
        """Dublin Core element - date resource expires.
        """
        expires = self.getField('expirationDate').get(self)
        # XXX None? CEILING_DATE
        return expires is None and 'None' or expires.ISO()

    security.declareProtected(CMFCorePermissions.View, 'Date')
    def Date(self):
        """
        Dublin Core element - default date
        """
        # Return effective_date if specifically set, modification date
        # otherwise
        effective = self.getField('effectiveDate').get(self)
        if effective is None:
            effective = self.modified()
        return effective is None and DateTime() or effective.ISO()

    security.declareProtected(CMFCorePermissions.View, 'Format')
    def Format(self):
        """cmf/backward compat
        Dublin Core element - resource format
        """
        # FIXME: get content type from marshaller
        return self.getContentType()

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'setFormat')
    def setFormat(self, value):
        """cmf/backward compat: ignore setFormat"""
        self.setContentType(value)

    def Identifer(self):
        """ dublin core getId method"""
        return self.getId()

    #  DublinCore utility methods #############################################

    security.declareProtected(CMFCorePermissions.View, 'contentEffective')
    def contentEffective(self, date):
        """Is the date within the resource's effective range?
        """
        effective = self.getField('effectiveDate').get(self)
        expires = self.getField('expirationDate').get(self)
        pastEffective = ( effective is None or effective <= date )
        beforeExpiration = ( expires is None or expires >= date )
        return pastEffective and beforeExpiration

    security.declareProtected(CMFCorePermissions.View, 'contentExpired')
    def contentExpired(self, date=None):
        """ Is the date after resource's expiration """
        if not date:
            # XXX we need some unittesting for this
            date = DateTime()
        expires = self.getField('expirationDate').get(self)
        if not expires:
            expires = CEILING_DATE
        return expires <= date

    #  CatalogableDublinCore methods ##########################################

    security.declareProtected(CMFCorePermissions.View, 'created')
    def created(self):
        """Dublin Core element - date resource created,
        returned as DateTime.
        """
        # allow for non-existent creation_date, existed always
        created = self.getField('creation_date').get(self)
        return created is None and FLOOR_DATE or created

    security.declareProtected(CMFCorePermissions.View, 'modified')
    def modified(self):
        """Dublin Core element - date resource last modified,
        returned as DateTime.
        """
        modified = self.getField('modification_date').get(self)
        # XXX may return None
        return modified

    security.declareProtected(CMFCorePermissions.View, 'effective')
    def effective(self):
        """Dublin Core element - date resource becomes effective,
        returned as DateTime.
        """
        effective = self.getField('effectiveDate').get(self)
        return effective is None and FLOOR_DATE or effective

    security.declareProtected(CMFCorePermissions.View, 'expires')
    def expires(self):
        """Dublin Core element - date resource expires,
        returned as DateTime.
        """
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

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'notifyModified')
    def notifyModified(self):
        """
        Take appropriate action after the resource has been modified.
        For now, change the modification_date.
        """
        # XXX This could also store the id of the user doing modifications.
        self.setModificationDate(DateTime())

    # XXX Could this be simply protected by ModifyPortalContent ?
    security.declarePrivate('setModificationDate')
    def setModificationDate(self, modification_date=None):
        """Set the date when the resource was last modified.
        When called without an argument, sets the date to now.
        """
        if modification_date is None:
            modified = DateTime()
        else:
            modified = self._datify(modification_date)
        self.getField('modification_date').set(self, modified)

    security.declarePrivate('setCreationDate')
    def setCreationDate(self, creation_date=None):
        """Set the date when the resource was created.
        When called without an argument, sets the date to now.
        """
        if creation_date is None:
            created = DateTime()
        else:
            created = self._datify(creation_date)
        self.getField('creation_date').set(self, created)

    security.declarePrivate( '_datify' )
    def _datify(self, date):
        """Try to convert something into a DateTime instance or None
        """
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
    security.declareProtected(CMFCorePermissions.View, 'Publisher')
    def Publisher(self):
        """Dublin Core element - resource publisher
        """
        # XXX: fixme using 'portal_metadata'
        return 'No publisher'

    security.declareProtected(CMFCorePermissions.View, 'ModificationDate')
    def ModificationDate(self):
        """ Dublin Core element - date resource last modified.
        """
        modified = self.modified()
        return modified is None and DateTime() or modified.ISO()

    security.declareProtected(CMFCorePermissions.View, 'Type')
    def Type(self):
        """Dublin Core element - Object type"""
        if hasattr(aq_base(self), 'getTypeInfo'):
            ti = self.getTypeInfo()
            if ti is not None:
                return ti.Title()
        return self.meta_type

    security.declareProtected(CMFCorePermissions.View, 'Identifier')
    def Identifier(self):
        """Dublin Core element - Object ID"""
        # XXX: fixme using 'portal_metadata' (we need to prepend the
        #      right prefix to self.getPhysicalPath().
        return self.absolute_url()

    security.declareProtected(CMFCorePermissions.View, 'listContributors')
    def listContributors(self):
        """Dublin Core element - Contributors"""
        return self.Contributors()

    security.declareProtected(CMFCorePermissions.ModifyPortalContent,
                              'addCreator')
    def addCreator(self, creator=None):
        """ Add creator to Dublin Core creators.
        """
        if creator is None:
            mtool = getToolByName(self, 'portal_membership')
            creator = mtool.getAuthenticatedMember().getId()

        # call self.listCreators() to make sure self.creators exists
        if creator and not creator in self.listCreators():
            self.setCreators(self.creators + (creator, ))

    security.declareProtected(CMFCorePermissions.View, 'listCreators')
    def listCreators(self):
        """ List Dublin Core Creator elements - resource authors.
        """
        creators = self.Schema()['creators']
        if not creators.get(self):
            # for content created with CMF versions before 1.5
            owner = self.getOwner()
            if hasattr(owner, 'getId'):
                creators.set(self, (owner.getId(),))
            else:
                creators.set(self, ())

        return creators.get(self)

    security.declareProtected(CMFCorePermissions.View, 'Creator')
    def Creator(self):
        """ Dublin Core Creator element - resource author.
        """
        creators = self.listCreators()
        return creators and creators[0] or ''

    #
    #  DublinCore utility methods
    #

    security.declareProtected(CMFCorePermissions.View, 'content_type')
    def content_type(self):
        """ WebDAV needs this to do the Right Thing (TM).
        """
        return self.Format()
    #
    #  CatalogableDublinCore methods
    #

    security.declareProtected(CMFCorePermissions.View, 'getMetadataHeaders')
    def getMetadataHeaders(self):
        """ Return RFC-822-style headers.
        """
        return [
            ('Title', self.Title()),
            ('Subject', ', '.join(self.Subject())),
            ('Publisher', self.Publisher()),
            ('Description', self.Description()),
            ('Contributors', '; '.join(self.Contributors())),
            ('Effective_date', self.EffectiveDate()),
            ('Expiration_date', self.ExpirationDate()),
            ('Type', self.Type()),
            ('Format', self.Format()),
            ('Language', self.Language()),
            ('Rights', self.Rights()),
            ]

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

ExtensibleMetadataSchema = ExtensibleMetadata.schema

__all__ = ('ExtensibleMetadata', 'ExtensibleMetadataSchema', )
