from cStringIO import StringIO
from Products.CMFPlone.Portal import addPolicy
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.Expression import Expression
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.DirectoryView import addDirectoryViews, registerDirectory
from Products.CMFPlone.CustomizationPolicy import DefaultCustomizationPolicy
from Products.Archetypes.Extensions.Install import install as installArchetypes
import sys


class ArchetypeCustomizationPolicy(DefaultCustomizationPolicy):
    """ Install Plone with the Archetypes Package """

    def __init__(self, i18n=0):
        self.i18n = i18n
    
    def customize(self, portal):
        # do the base Default install, that gets
        # most of it right
        DefaultCustomizationPolicy.customize(self, portal)
        outStr = doCustomization(portal, self.i18n)
            
        print >> sys.stdout, outStr

def doCustomization(self, i18n):
    out = StringIO()

    # Always include demo types
    result = installArchetypes(self, include_demo=1)
    print >>out, result
    
    updatePortalProps(self, out)
    updateActions(self, out)
    if i18n:
        setI18NIndexes(self, out)
    
    return out.getvalue()

def setI18NIndexes(portal, out):
    # we need to commit the subtransaction here since we'll have to access some
    # script in the skin path (getContentLanguage)
    get_transaction().commit(1)

    # install the I18NTextIndexNG product
    from Products.I18NTextIndexNG.Extensions.Install import install
    print >>sys.stderr, install(portal)
    # then set indexes
    catalog = getToolByName(portal, 'portal_catalog')
    for accessor in ('Title', 'Description', 'SearchableText'):
        try:
            catalog.delIndex(accessor)
        except:
            pass
        catalog.addIndex(accessor, 'I18NTextIndexNG', extra=None)
        catalog.manage_reindexIndex(ids=(accessor,))
        print >>out, 'Set I18NTextIndexNG index for %s' % accessor
    # add the language selector box
    left_slots = portal.getProperty('left_slots', ())
    portal._updateProperty('left_slots',
                         left_slots + ('here/i18n_slot/macros/i18nContentBox',))


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
    addPolicy('I18N Archetypes Site', ArchetypeCustomizationPolicy(1))
