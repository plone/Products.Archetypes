import os.path
__version__ = open(os.path.join(__path__[0], 'version.txt')).read().strip()

import sys
import bbb

from Products.Archetypes.config import *
from Products.Archetypes.utils import DisplayList, getPkgInfo
import Products.Archetypes.patches

from AccessControl import ModuleSecurityInfo
from AccessControl import allow_class
from Products.CMFCore import permissions
from Products.CMFCore.DirectoryView import registerDirectory
try:
    from Products.CMFCore import ISiteRoot
    from Products.GenericSetup import EXTENSION, profile_registry
    HAS_GENERICSETUP = True
except ImportError:
    HAS_GENERICSETUP = False


###
## security
###
# make log and log_exc public
ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log')
ModuleSecurityInfo('Products.Archetypes.debug').declarePublic('log_exc')

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
# XXX: Check if we need these imports here, after version checks are removed
this_module = sys.modules[__name__]
import Products.MimetypesRegistry
import Products.PortalTransforms
import Products.validation

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

    if HAS_GENERICSETUP:
        profile_registry.registerProfile('Archetypes',
                'Archetypes',
                'Extension profile for default Archetypes setup',
                'profiles/default',
                'Archetypes',
                EXTENSION,
                for_=ISiteRoot)

