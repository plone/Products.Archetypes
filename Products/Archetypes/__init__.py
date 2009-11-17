import sys
import bbb

from Products.Archetypes.config import *
from Products.Archetypes.utils import DisplayList

from AccessControl import ModuleSecurityInfo
from AccessControl import allow_class, allow_module
from Products.CMFCore import permissions

###
## security
###
# make log and log_exc public
allow_module('Products.Archetypes.utils')

ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log')
ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log_exc')
ModuleSecurityInfo('Products.Archetypes.mimetype_utils').declarePublic('getAllowableContentTypes')
ModuleSecurityInfo('Products.Archetypes.mimetype_utils').declarePublic('getAllowedContentTypes')
ModuleSecurityInfo('Products.Archetypes.mimetype_utils').declarePublic('getForbiddenContentTypes')
ModuleSecurityInfo('Products.Archetypes.mimetype_utils').declarePublic('getDefaultContentType')
ModuleSecurityInfo('Products.Archetypes.mimetype_utils').declareProtected(permissions.ManagePortal, 'setForbiddenContentTypes')
ModuleSecurityInfo('Products.Archetypes.mimetype_utils').declareProtected(permissions.ManagePortal, 'setDefaultContentType')

# Import "PloneMessageFactory as _" to create messages in plone domain
# duplicated here so we don't add a dependency on CMFPlone
from zope.i18nmessageid import MessageFactory
PloneMessageFactory = MessageFactory('plone')
ModuleSecurityInfo('Products.Archetypes').declarePublic('PloneMessageFactory')

# make DisplayList accessible from python scripts and others objects executed
# in a restricted environment
allow_class(DisplayList)

# Allow import of NotFound exception
ModuleSecurityInfo('zExceptions').declarePublic('NotFound')

###
# register tools and content types
###
from Products.Archetypes.ArchetypeTool import \
    process_types, listTypes, fixAfterRenameType
from Products.Archetypes.ArchetypeTool import ArchetypeTool
ATToolModule = sys.modules[ArchetypeTool.__module__] # mpf :|
from Products.Archetypes.ArchTTWTool import ArchTTWTool
from Products.Archetypes.ReferenceEngine import ReferenceCatalog as RefTool
from Products.Archetypes.UIDCatalog import UIDCatalog as UIDTool


tools = (
    ArchetypeTool,
    ArchTTWTool,
    RefTool,
    UIDTool,
    )

types_globals=globals()

def initialize(context):
    from Products.CMFCore import utils

    utils.ToolInit("%s Tool" % PKG_NAME, tools=tools,
                   icon="tool.gif",
                   ).initialize(context)

    if REGISTER_DEMO_TYPES:
        import Products.Archetypes.examples

        content_types, constructors, ftis = process_types(
            listTypes(PKG_NAME), PKG_NAME)

        utils.ContentInit(
            '%s Content' % PKG_NAME,
            content_types = content_types,
            permission = permissions.AddPortalContent,
            extra_constructors = constructors,
            fti = ftis,
            ).initialize(context)
    try:
        from Products.CMFCore.FSFile import FSFile
        from Products.CMFCore.DirectoryView import registerFileExtension
        registerFileExtension('xsl', FSFile)
        registerFileExtension('xul', FSFile)
    except ImportError:
        pass
