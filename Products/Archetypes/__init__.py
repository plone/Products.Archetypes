from AccessControl import ModuleSecurityInfo
from AccessControl import allow_class
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore.TypesTool import TypesTool, typeClasses
from config import *
from debug import log, log_exc

# Bootstrap generator and validation package for users installing them in
# the Products directory
try:
    import generator
    import validation
except ImportError:
    import sys
    from os.path import dirname
    sys.path.append(dirname(__path__[0]))
    import generator
    import validation

# Bootstrap Zope-dependent validators
import Validators

# look if BTreeFolder2 is installed, warn if not
try:
    import Products.BTreeFolder2
except ImportError:
    log_exc("""BTreeFolder2 was not available. You will not be able to use BaseBTreeFolder.""")


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
from utils import DisplayList
allow_class(DisplayList)


###
# register tools and content types
###
registerDirectory('skins', globals())

from ArchetypeTool import ArchetypeTool, \
                          registerType, \
                          process_types, \
                          listTypes
from ArchTTWTool import ArchTTWTool

tools = (
    ArchetypeTool,
    ArchTTWTool,
    )


types_globals=globals()

def initialize(context):
    from Products.CMFCore import utils
##    from Extensions import ArchetypeSite

##    ArchetypeSite.register(context, globals())

    utils.ToolInit("%s Tool" % PKG_NAME, tools=tools,
                   product_name=PKG_NAME,
                   icon="tool.gif",
                   ).initialize(context)

    if REGISTER_DEMO_TYPES:
        import examples

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
