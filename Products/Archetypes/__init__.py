import sys

from Products.Archetypes.config import *
from Products.Archetypes.utils import DisplayList

from AccessControl import ModuleSecurityInfo
from AccessControl import allow_class
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.DirectoryView import registerDirectory

###
## security
###
# make log and log_exc public
ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log')
ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log_exc')

# Plone compatibility in plain CMF. Templates should use IndexIterator from
# Archetypes and not from CMFPlone
try:
    from Products.CMFPlone.PloneUtilities import IndexIterator
except:
    from PloneCompat import IndexIterator
allow_class(IndexIterator)

# make DisplayList accessible from python scripts and others objects executed
# in a restricted environment
allow_class(DisplayList)


###
# register tools and content types
###
registerDirectory('skins', globals())

from Products.Archetypes.ArchetypeTool import ArchetypeTool, \
     process_types, listTypes, fixAfterRenameType
ATToolModule = sys.modules[ArchetypeTool.__module__] # mpf :|
from Products.Archetypes.ArchTTWTool import ArchTTWTool

tools = (
    ArchetypeTool,
    ArchTTWTool,
    )

types_globals=globals()

def initialize(context):
    from Products.CMFCore import utils

    utils.ToolInit("%s Tool" % PKG_NAME, tools=tools,
                   product_name=PKG_NAME,
                   icon="tool.gif",
                   ).initialize(context)

    if REGISTER_DEMO_TYPES:
        import Products.Archetypes.examples

        content_types, constructors, ftis = process_types(
            listTypes(PKG_NAME), PKG_NAME)

        utils.ContentInit(
            '%s Content' % PKG_NAME,
            content_types = content_types,
            permission = CMFCorePermissions.AddPortalContent,
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
