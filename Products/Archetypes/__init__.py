import os.path
__version__ = open(os.path.join(__path__[0], 'version.txt')).read().strip()

import sys

from Products.Archetypes.config import *
from Products.Archetypes.utils import DisplayList, getPkgInfo
import Products.Archetypes.patches

from AccessControl import ModuleSecurityInfo
from AccessControl import allow_class
try:
    from Products.CMFCore import permissions as CMFCorePermissions
except ImportError:
    from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.DirectoryView import registerDirectory

from zLOG import LOG, PROBLEM

###
## security
###
# make log and log_exc public
ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log')
ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log_exc')

# Zope 2.8-style transaction module
# BBB: Zope 2.7
try:
    import Zope2
except ImportError:
    import transaction_ as transaction
else:
    import transaction

# Plone compatibility in plain CMF. Templates should use IndexIterator from
# Archetypes and not from CMFPlone
from PloneCompat import IndexIterator
allow_class(IndexIterator)

from PloneCompat import transaction_note
ModuleSecurityInfo('Products.Archetypes').declarePublic('transaction_note')

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


###
# Test dependencies
###
this_module = sys.modules[__name__]
import Products.MimetypesRegistry
import Products.PortalTransforms
import Products.generator
import Products.validation

# odd dependency checking :-/
mtr_info = getPkgInfo(Products.MimetypesRegistry)
pt_info = getPkgInfo(Products.PortalTransforms)
gen_info = getPkgInfo(Products.generator)
val_info = getPkgInfo(Products.validation)

at_version = __version__
for info in (mtr_info, pt_info, gen_info, val_info, ):
    if not hasattr(info, 'at_versions'):
        raise RuntimeError('The product %s has no at_versions assigend. ' \
                           'Please update to a newer version.' % info.modname)
    if at_version not in info.at_versions:
        raise RuntimeError('The current Archetypes version %s is not in list ' \
                           'of compatible versions for %s!\nList: %s' % \
                           (at_version, info.modname, info.at_versions)
                          )

###
# Tools
###

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

    from Products.Archetypes.customizationpolicy import registerPolicy
    registerPolicy(context)

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
