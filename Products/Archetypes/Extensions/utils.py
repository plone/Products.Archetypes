from Products.CMFCore.TypesTool import  FactoryTypeInformation
from Products.CMFCore.DirectoryView import addDirectoryViews, registerDirectory, \
     createDirectoryView, manage_listAvailableDirectories
from Products.CMFCore.utils import getToolByName, minimalpath
from Products.CMFCore.ActionInformation import ActionInformation
from Products.CMFCore.Expression import Expression

from Products.Archetypes.debug import log, log_exc
from Products.Archetypes.utils import findDict
from Products.Archetypes import types_globals
from Products.Archetypes.interfaces.base import IBaseObject
from OFS.ObjectManager import BadRequestException
from Globals import package_home
import sys, traceback, os
from types import *

try:
    from Products.CMFPlone.Configuration import getCMFVersion
except ImportError:
    # Configuration and getCMFVersion come with Plone 1.1
    def getCMFVersion():
        from os.path import join
        from Globals import package_home
        from Products.CMFCore import cmfcore_globals

        path=join(package_home(cmfcore_globals),'version.txt')
        file=open(path, 'r')
        _version=file.read()
        file.close()
        return _version.strip()

def install_tools(self, out):
    if not hasattr(self, "archetype_tool"):
        addTool = self.manage_addProduct['Archetypes'].manage_addTool
        addTool('Archetype Tool')

        ##Test some of the templating code
        at = getToolByName(self, 'archetype_tool')
        at.registerTemplate('base_view', "Normal View")


    #and the tool uses an index
    catalog = getToolByName(self, 'portal_catalog')
    try:
        catalog.addIndex('UID', 'FieldIndex', extra=None)
    except:
        pass

    try:
        if not 'UID' in catalog.schema():
            catalog.addColumn('UID')
    except:
        print >> out, ''.join(traceback.format_exception(*sys.exc_info()))
        print >> out, "Problem updating catalog for UIDs"

    try:
        catalog.manage_reindexIndex(ids=('UID',))
    except:
        pass


def install_subskin(self, out, globals=types_globals, product_skins_dir='skins'):
    skinstool=getToolByName(self, 'portal_skins')

    fullProductSkinsPath = os.path.join(package_home(globals), product_skins_dir)
    productSkinsPath = minimalpath(fullProductSkinsPath)
    registered_directories = manage_listAvailableDirectories()
    if productSkinsPath not in registered_directories:
        registerDirectory(product_skins_dir, globals)
    try:
        addDirectoryViews(skinstool, product_skins_dir, globals)
    except BadRequestException, e:
        pass  # directory view has already been added

    files = os.listdir(fullProductSkinsPath)
    for productSkinName in files:
        if os.path.isdir(os.path.join(fullProductSkinsPath, productSkinName)) \
               and productSkinName != 'CVS':
            for skinName in skinstool.getSkinSelections():
                path = skinstool.getSkinPath(skinName)
                path = [i.strip() for i in  path.split(',')]
                try:
                    if productSkinName not in path:
                        path.insert(path.index('custom') +1, productSkinName)
                except ValueError:
                    if productSkinName not in path:
                        path.append(productSkinName)
                path = ','.join(path)
                skinstool.addSkinSelection(skinName, path)


def install_types(self, out, types, package_name):
    typesTool = getToolByName(self, 'portal_types')
    for type in types:
        try:
            typesTool._delObject(type.__name__)
        except:
            pass

        typeinfo_name="%s: %s" % (package_name, type.__name__)

        typesTool.manage_addTypeInformation(FactoryTypeInformation.meta_type,
                                                id=type.__name__,
                                                typeinfo_name=typeinfo_name)
        # set the human readable title explicitly
        t = getattr(typesTool, type.__name__, None)
        if t:
            t.title = type.archetype_name

def install_validation(self, out, types):
    form_tool = getToolByName(self, 'portal_form')
    type_tool = getToolByName(self, 'portal_types')

    # No validation on references
    form_tool.setValidators('reference_edit', [])

    # Default validation for types
    form_tool.setValidators("base_edit", ["validate_base"])
    form_tool.setValidators("base_metadata", ["validate_base"])


def install_navigation(self, out, types):
    nav_tool = getToolByName(self, 'portal_navigation')
    type_tool = getToolByName(self, 'portal_types')

    #Generic Edit
    script = "content_edit"
    nav_tool.addTransitionFor('default', "content_edit", 'failure', 'action:edit')
    nav_tool.addTransitionFor('default', "content_edit", 'success', 'action:view')

    nav_tool.addTransitionFor('default', "base_edit", 'failure', 'base_edit')
    nav_tool.addTransitionFor('default', "base_edit", 'success', 'script:content_edit')

    nav_tool.addTransitionFor('default', "base_metadata", 'failure', 'base_metadata')
    nav_tool.addTransitionFor('default', "base_metadata", 'success', 'script:content_edit')

    #And References
    nav_tool.addTransitionFor('default', 'reference_edit', 'success', 'pasteReference')
    nav_tool.addTransitionFor('default', 'reference_edit', 'failure', 'url:reference_edit')




def install_actions(self, out, types):
    typesTool = getToolByName(self, 'portal_types')
    for portal_type in types:
        if 'actions' in portal_type.installMode:
            typeInfo = getattr(typesTool, portal_type.__name__)
            if hasattr(portal_type,'actions'):
                #Look for each action we define in portal_type.actions
                #in typeInfo.action replacing it if its there and
                #just adding it if not
                if getattr(portal_type,'include_default_actions',1):
                    new = list(typeInfo._actions)
                else:
                    # if no standard actions are wished - dont display them
                    new=[]

                cmfver=getCMFVersion()

                for action in portal_type.actions:
                    if cmfver[:7] >= "CMF-1.4" and cmfver != 'Unreleased': 
                        #then we know actions are defined new style as ActionInformations
                        hits = [a for a in new if a.id==action['id']]
                        
                        #change action and condition into expressions,
                        #if they are still strings
                        if action.has_key('action') and type(action['action']) in (type(''), type(u'')):
                            action['action']=Expression(action['action'])
                        if action.has_key('condition') and type(action['condition']) in (type(''), type(u'')):
                            action['condition']=Expression(action['condition'])
                        if hits:
                            hits[0].__dict__.update(action)
                        else:
                            if action.has_key('name'):
                                action['title']=action['name']
                                del action['name']

                            new.append (ActionInformation(**action))
                    else:
                        hit = findDict(new, 'id', action['id'])
                        if hit:
                            hit.update(action)
                        else:
                            new.append(action)

                typeInfo._actions = tuple(new)
                typeInfo._p_changed = 1

            if hasattr(portal_type,'factory_type_information'):
                typeInfo.__dict__.update(portal_type.factory_type_information)
                typeInfo._p_changed = 1

def install_indexes(self, out, types):
    catalog = getToolByName(self, 'portal_catalog')

    for cls in types:
        if 'indexes' not in cls.installMode:
            continue

        for field in cls.schema.fields():
            if field.index:
                if type(field.index) is StringType:
                    index = (field.index,)
                else:
                    index = field.index

                for alternative in index:
                    installed = None
                    schema = alternative.split(':', 1)
                    if len(schema) == 2 and schema[1] == 'schema':
                        try:
                            if ischema and field.accessor not in catalog.schema():
                                catalog.addColumn(field.accessor)
                        except:
                            pass

                    parts = alternative.split('|')

                    for itype in parts:
                        try:
                            #Check for the index and add it if missing
                            catalog.addIndex(field.accessor, itype,
                                             extra=None)
                            catalog.manage_reindexIndex(ids=(field.accessor,))
                        except:
                            pass
                        else:
                            installed = 1
                            break

                    if installed:
                        break



def isPloneSite(self):
    # we should just define a single attr for this
    if self.__class__.__name__ == "PloneSite":
        return 1
    for base in self.__class__.__bases__:
        if base.__name__ == "PloneSite":
            return 1
    return 0


def filterTypes(self, out, types, package_name):
    typesTool = getToolByName(self, 'portal_types')

    filtered_types = []

    for rti in types:
        t = rti['klass']

        typeinfo_name="%s: %s" % (package_name, t.__name__)
        info = typesTool.listDefaultTypeInformation()
        found = 0
        for (name, ft) in info:
            if name == typeinfo_name:
                found = 1
                break

        if not found:
            print >> out, '%s is not a registered Type Information' % typeinfo_name
            continue

        if IBaseObject.isImplementedByInstancesOf(t):
            filtered_types.append(t)
        else:
            print >> out, """%s doesnt implements IBaseObject. Possible misconfiguration.""" % repr(t) + \
                          """ Check if your class has an '__implements__ = IBaseObject'""" + \
                          """ (or IBaseContent, or IBaseFolder)"""

    return filtered_types


def setupEnvironment(self, out, types,
                     package_name,
                     globals=types_globals,
                     product_skins_dir='skins'):

    types = filterTypes(self, out, types, package_name)
    install_tools(self, out)
    install_subskin(self, out, globals, product_skins_dir)

    install_indexes(self, out, types)
    install_actions(self, out, types)

    if isPloneSite(self):
        install_validation(self, out, types)
        install_navigation(self, out, types)


## The master installer
def installTypes(self,
                 out,
                 types,
                 package_name,
                 globals=types_globals,
                 product_skins_dir='skins'):
    """Use this for your site with your types"""
    ftypes = filterTypes(self, out, types, package_name)
    install_types(self, out, ftypes, package_name)
    #Pass the unfiltered types into setup as it does that on its own
    setupEnvironment(self, out, types, package_name, globals, product_skins_dir)
