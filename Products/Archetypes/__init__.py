from AccessControl import ModuleSecurityInfo
from Globals import InitializeClass
from Products.CMFCore  import CMFCorePermissions
from Products.CMFCore.DirectoryView import registerDirectory
from config import *
from debug import log

registerDirectory('skins', globals())

from ArchetypeTool import ArchetypeTool, \
                          registerType, \
                          process_types
from ArchetypeTool import listTypes as baseListTypes

tools = (
    ArchetypeTool,
    )

###
## back compat type registration
###
def listTypes(package=None):
    #log("Deprecated listTypes called", deep=5)
    value = baseListTypes(package)
    value = [v['klass'] for v in value]
    return value

###
## security
###
ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log')
ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log_exc')

def initialize(context):
    from Products.CMFCore import utils
    from Extensions import ArchetypeSite

    ArchetypeSite.register(context, globals())

    ## This could all go away, in a real site, we wouldn't include the
    ## demo types
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

types_globals=globals()
