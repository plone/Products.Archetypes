from Products.CMFPlone.Portal import addPolicy
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.DirectoryView import addDirectoryViews, registerDirectory

from Products.CMFPlone.CustomizationPolicy import DefaultCustomizationPolicy

from Products.Archetypes import listTypes, types_globals
from Products.Archetypes.Extensions.Install import install as installArchetypes
import sys


class ArchetypeCustomizationPolicy(DefaultCustomizationPolicy):
    """ Install Plone with the Archetypes Package """

    def customize(self, portal):
        # do the base Default install, that gets
        # most of it right
        DefaultCustomizationPolicy.customize(self, portal)

        outStr = doCustomization(portal)
        #print >> sys.stdout, outStr
        

def doCustomization(self):
    from StringIO import StringIO
    out = StringIO()

    #Make sure to include the demo types for now
    import Products.Archetypes.config
    Products.Archetypes.config.INCLUDE_DEMO_TYPES = 1
    
    result = installArchetypes(self)
    print >>out, result
    
    updatePortalProps(self, out)
    updateActions(self, out)
    
    return out.getvalue()



#
# set the portal properties
#
def updatePortalProps(portal, out):
    # customize slots
    # add the slots to the portal folder
    left_slots=( 
        'here/navigation_tree_slot/macros/navigationBox',
        'here/login_slot/macros/loginBox',
        'here/about_slot/macros/aboutBox',
        'here/reference_slot/macros/referenceBox',
        )
    right_slots=(
        'here/calendar_slot/macros/calendarBox',
        'here/workflow_review_slot/macros/review_box',
        )
    
    portal._updateProperty('left_slots', left_slots)
    portal._updateProperty('right_slots', right_slots)
    portal.portal_properties.site_properties._updateProperty('localTimeFormat', '%b. %d, %y')
    portal.portal_properties.site_properties._updateProperty('localLongTimeFormat', '%b. %d, %y %I:%M %p')
    

def updateActions(portal, out):
    actions_tool=getToolByName(portal, 'portal_actions')

##     actions_tool.addAction('reference',
##                            'Reference',
##                            'string:folder_copy:method',
##                            '',
##                            CMFCorePermissions.ModifyPortalContent,
##                            'folder_buttons',
##                            )
    
            
    
def register(context, app_state):
    addPolicy('Archetypes Site', ArchetypeCustomizationPolicy())
