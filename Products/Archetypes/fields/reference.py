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

# common imports
from types import StringType
from cStringIO import StringIO
from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from Acquisition import aq_parent
from Acquisition import aq_inner
from ComputedAttribute import ComputedAttribute
from ZPublisher.HTTPRequest import FileUpload
from Products.CMFCore import CMFCorePermissions
from Products.Archetypes.interfaces.layer import ILayerContainer
from Products.Archetypes.registries import registerField
from Products.Archetypes.registries import registerPropertyType
from Products.Archetypes.storages import AttributeStorage
from Products.Archetypes.lib.utils import shasattr
from Products.Archetypes.lib.utils import mapply
from Products.Archetypes.lib.vocabulary import DisplayList
from Products.Archetypes.fields.base import Field
from Products.Archetypes.fields.base import ObjectField

# field specific imports
from types import ListType, TupleType
from Products.CMFCore.utils import getToolByName
from Products.Archetypes.widgets import ReferenceWidget
from Products.Archetypes.lib.translate import translate
from Products.Archetypes.refengine.references import Reference
from Products.Archetypes.config import UID_CATALOG
from Products.Archetypes.config import REFERENCE_CATALOG
from Products.Archetypes.config import REFERENCE_ANNOTATION
from Products.Archetypes.config import STRING_TYPES

__docformat__ = 'reStructuredText'

class ReferenceField(ObjectField):
    """A field for creating references between objects.

    get() returns the list of objects referenced under the relationship
    set() converts a list of target UIDs into references under the
    relationship associated with this field.

    If no vocabulary is provided by you, one will be assembled based on
    allowed_types.
    """
    
    __implements__ = ObjectField.__implements__

    _properties = Field._properties.copy()
    _properties.update({
        'type' : 'reference',
        'default' : None,
        'widget' : ReferenceWidget,

        'relationship' : None, # required
        'allowed_types' : (),  # a tuple of portal types, empty means allow all
        'allowed_types_method' :None,
        'vocabulary_display_path_bound': 5, # if len(vocabulary) > 5, we'll
                                            # display path as well
        'vocabulary_custom_label': None, # e.g. "b.getObject().title_or_id()".
                                         # if given, this will
                                         # override display_path_bound
        'referenceClass' : Reference,
        'referenceReferences' : False,
        'callStorageOnSet': False,
        'index_method' : '_at_edit_accessor',
        })

    security  = ClassSecurityInfo()


    security.declarePrivate('get')
    def get(self, instance, aslist=False, **kwargs):
        """get() returns the list of objects referenced under the relationship
        """
        res = instance.getRefs(relationship=self.relationship)

        # singlevalued ref fields return only the object, not a list,
        # unless explicitely specified by the aslist option
        if not self.multiValued and not aslist:
            if res:
                assert len(res) == 1
                res = res[0]
            else:
                res = None

        return res

    security.declarePrivate('set')
    def set(self, instance, value, **kwargs):
        """Mutator.

        ``value`` is a list of UIDs or one UID string to which I will add a
        reference to. None and [] are equal.

        Keyword arguments may be passed directly to addReference(), thereby
        creating properties on the reference objects.
        """
        tool = getToolByName(instance, REFERENCE_CATALOG)
        targetUIDs = [ref.targetUID for ref in
                      tool.getReferences(instance, self.relationship)]

        if (not self.multiValued and value and
            type(value) not in (ListType, TupleType)):
            value = (value,)

        if not value:
            value = ()

        #convertobjects to uids if necessary
        uids=[]
        for v in value:
            if type(v) in STRING_TYPES:
                uids.append(v)
            else:
                uids.append(v.UID())

        add = [v for v in uids if v and v not in targetUIDs]
        sub = [t for t in targetUIDs if t not in uids]

        # tweak keyword arguments for addReference
        addRef_kw = kwargs.copy()
        addRef_kw.setdefault('referenceClass', self.referenceClass)
        if addRef_kw.has_key('schema'): del addRef_kw['schema']

        for uid in add:
            __traceback_info__ = (instance, uid, value, targetUIDs)
            # throws IndexError if uid is invalid
            tool.addReference(instance, uid, self.relationship, **addRef_kw)

        for uid in sub:
            tool.deleteReference(instance, uid, self.relationship)

        if self.callStorageOnSet:
            #if this option is set the reference fields's values get written
            #to the storage even if the reference field never use the storage
            #e.g. if i want to store the reference UIDs into an SQL field
            ObjectField.set(self, instance, self.getRaw(instance), **kwargs)

    security.declarePrivate('getRaw')
    def getRaw(self, instance, aslist=False, **kwargs):
        """Return the list of UIDs referenced under this fields
        relationship
        """
        rc = getToolByName(instance, REFERENCE_CATALOG)
        brains = rc(sourceUID=instance.UID(),
                    relationship=self.relationship)
        res = [b.targetUID for b in brains]
        if not self.multiValued and not aslist:
            if res:
                res = res[0]
            else:
                res = None
        return res

    security.declarePublic('Vocabulary')
    def Vocabulary(self, content_instance=None):
        """Use vocabulary property if it's been defined."""
        if self.vocabulary:
            return ObjectField.Vocabulary(self, content_instance)
        else:
            return self._Vocabulary(content_instance).sortedByValue()

    def _Vocabulary(self, content_instance):
        pairs = []
        pc = getToolByName(content_instance, 'portal_catalog')
        uc = getToolByName(content_instance, UID_CATALOG)
        purl = getToolByName(content_instance, 'portal_url')

        allowed_types = self.allowed_types
        allowed_types_method = getattr(self, 'allowed_types_method', None)
        if allowed_types_method:
            meth = getattr(content_instance,allowed_types_method)
            allowed_types = meth(self)

        skw = allowed_types and {'portal_type':allowed_types} or {}
        brains = uc.searchResults(**skw)

        if self.vocabulary_custom_label is not None:
            label = lambda b:eval(self.vocabulary_custom_label, {'b': b})
        elif len(brains) > self.vocabulary_display_path_bound:
            at = translate(domain='archetypes', msgid='label_at',
                                context=content_instance, default='at')
            label = lambda b:'%s %s %s' % (b.Title or b.id, at,
                                           b.getPath())
        else:
            label = lambda b:b.Title or b.id

        # The UID catalog is the correct catalog to pull this
        # information from, however the workflow and perms are not accounted
        # for there. We thus check each object in the portal catalog
        # to ensure it validity for this user.
        portal_base = purl.getPortalPath()
        path_offset = len(portal_base) + 1

        abs_paths = {}
        abs_path = lambda b, p=portal_base: '%s/%s' % (p, b.getPath())
        [abs_paths.update({abs_path(b):b}) for b in brains]

        pc_brains = pc(path=abs_paths.keys(), **skw)

        for b in pc_brains:
            b_path = b.getPath()
            # translate abs path to rel path since uid_cat stores
            # paths relative now
            path = b_path[path_offset:]
            # The reference field will not expose Refrerences by
            # default, this is a complex use-case and makes things too hard to
            # understand for normal users. Because of reference class
            # we don't know portal type but we can look for the annotation key in
            # the path
            if self.referenceReferences is False and \
               path.find(REFERENCE_ANNOTATION) != -1:
                continue

            # now check if the results from the pc is the same as in uc.
            # so we verify that b is a result that was also returned by uc,
            # hence the check in abs_paths.
            if abs_paths.has_key(b_path):
                uid = abs_paths[b_path].UID
                if uid is None:
                    # the brain doesn't have an uid because the catalog has a
                    # staled object. THAT IS BAD!
                    raise ReferenceException("Brain for the object at %s "\
                        "doesn't have an UID assigned with. Please update your"\
                        " reference catalog!" % b_path)
                pairs.append((uid, label(b)))

        if not self.required and not self.multiValued:
            no_reference = translate(domain='archetypes',
                                          msgid='label_no_reference',
                                          context=content_instance,
                                          default='<no reference>')
            pairs.insert(0, ('', no_reference))

        __traceback_info__ = (content_instance, self.getName(), pairs)
        return DisplayList(pairs)

    security.declarePublic('get_size')
    def get_size(self, instance):
        """Get size of the stored data used for get_size in BaseObject
        """
        return 0

registerField(ReferenceField,
              title='Reference',
              description=('Used for storing references to '
                           'other Archetypes Objects'))

