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

from Interface import Interface, Attribute

class IBaseObject(Interface):
    """ The most basic Archetypes-based implementation
    """

    #XXX windows is strange
    #schema = Attribute('schema', 'Schema of the object')
    #installMode = Attribute('installMode', 'Used for installation. List of actions to perform.')

    #typeDescription = Attribute('Type description used for base_edit')
    #typeDescMsgId = Attribute('I18N message id for type description')

    def getId():
        """Get the object id
        """

    def setId(value):
        """Set the object id
        """

    def Type():
        """Dublin Core element - Object type

        this method is redefined in ExtensibleMetadata but we need this
        at the object level (i.e. with or without metadata) to interact
        with the uid catalog
        """

    def getField(key, wrapped=False):
        """Get a field by id
        """

    def getWrappedField(key):
        """Get a field by id which is explicitly wrapped
        """

    def getDefault(field):
        """Get default value for a field by id
        """

    def isBinary(key):
        """Check if an element is binary
        """

    def isTransformable(name):
        """Returns wether a field is transformable
        """

    def widget(field_name, mode="view", field=None, **kwargs):
        """Returns the rendered widget
        """

    def getContentType(key):
        """Content type for a field by key
        """

    def setContentType(value):
        """Sets the content type of the primary field
        """

    def getPrimaryField():
        """The primary field is some object that responds to
        PUT/manage_FTPget events.
        """

    def get_portal_metadata(field):
        """Returns the portal_metadata for a field
        """

    def Vocabulary(key):
        """Vocabulary for a field by key
        """

    def setDefaults():
        """Set default values for the fields
        """

    def update(**kwargs):
        """Update all fields and reindexObject
        """

    def edit(**kwargs):
        """Alias for update(**kwargs*)
        """

    def validate_field(name, value, errors):
        """Write a method: validate_foo(new_value) -> "error" or None

        If there is a validate method defined for a given field invoke it by name
        name -- the name to register errors under
        value -- the proposed new value
        errors -- dict to record errors in
        """

    def pre_validate(REQUEST, errors):
        """Pre-validation hook
        """

    def post_validate(REQUEST, errors):
        """Post-validation hook
        """

    def validate(REQUEST, errors):
        """Validate fields
        """

    def SearchableText():
        """Full indexable text
        """

    def getCharset():
        """ Return site default charset, or utf-8
        """

    def get_size():
        """Used for FTP and apparently the ZMI now too
        """

    def processForm(data=1, metadata=0, REQUEST=None, values=None):
        """Process the schema looking for data in the form
        """

    def Schemata():
        """Returns the Schemata for the Object
        """

    def addSubObjects(objects, REQUEST=None):
        """Add a dictionary of objects to the session
        """

    def getSubObject(name, REQUEST, RESPONSE=None):
        """Get a dictionary of objects from the session
        """

class IBaseContent(IBaseObject):
    """Contentish base interface marker

    BaseContent is subclassing the following classes, too:

    Products.Archetypes.Referenceable.Referenceable
    Products.Archetypes.CatalogMultiplex.CatalogMultiplex
    Products.CMFCore.PortalContent.PortalContent
    OFS.History.Historicall
    """


class IBaseFolder(IBaseObject):
    """Folderish base interface marker

    BaseFolder is subclassing the following classes, too:

    Products.CMFDefault.SkinnedFolder.SkinnedFolder
    OFS.Folder.Folder
    """

    def listFolderContents(spec=None, contentFilter=None, suppressHiddenFiles=0):
        """
        Optionally you can suppress 'hidden' files, or files that begin with '.'
        """

    def folderlistingFolderContents(spec=None, contentFilter=None,
                                    suppressHiddenFiles=0 ):
        """
        Calls listFolderContents in protected only by ACI so that folder_listing
        can work without the List folder contents permission, as in CMFDefault
        """

class IBaseUnit(Interface):
    """
    """

    def update(data, instance, **kw):
        """
        """

    def transform(instance, mt):
        """Takes a mimetype so object.foo.transform('text/plain') should return
        a plain text version of the raw content

        return None if no data or if data is untranformable to desired output
        mime type
        """

    def isBinary():
        """return true if this contains a binary value, else false"""

    def get_size():
        """
        """

    def getRaw(encoding=None, instance=None):
        """Return encoded raw value
        """

    def portalEncoding(instance):
        """Return the default portal encoding, using an external python script
        (look the archetypes skin directory for the default implementation)
        """

    def getContentType():
        """Return the imimetype object for this BU
        """

    def setContentType(instance, value):
        """
        """

    def content_type():
        """
        """

    def getFilename():
        """
        """

    def setFilename(filename):
        """
        """

    def index_html(REQUEST, RESPONSE):
        """download method
        """
