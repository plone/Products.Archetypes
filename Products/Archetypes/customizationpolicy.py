"""Archetypes customization policy for Plone sites

Based on the multilingual policy from Plone Solutions
"""

__author__  = 'Christian Heimes'
__docformat__ = 'restructuredtext'

from StringIO import StringIO

from Products.CMFPlone.Portal import addPolicy
from Products.CMFCore.utils import getToolByName
from Products.CMFPlone.CustomizationPolicy import DefaultCustomizationPolicy
from Products.Archetypes.utils import shasattr

PRODUCTS = ('MimetypesRegistry', 'PortalTransforms', 'Archetypes', )

class ArchetypesSitePolicy(DefaultCustomizationPolicy):
    """Site policy for SA
    """

    def customize(self, portal):
        DefaultCustomizationPolicy.customize(self, portal)
        out = StringIO()
        self.installArchetypes(portal, out)
        return out.getvalue()
    
    def installArchetypes(self, portal, out):
        """Install Archetypes with all dependencies
        """
        print >>out, 'Installing Archetypes ...'
        qi = getToolByName(portal, 'portal_quickinstaller')
        for product in PRODUCTS:
            if not qi.isProductInstalled(product):
                qi.installProduct(product)
                # Refresh skins
                if shasattr(portal, '_v_skindata'):
                    portal._v_skindata = None
                if shasattr(portal, 'setupCurrentSkin'):
                    portal.setupCurrentSkin()
                print >>out, '   Installed %s' % product
            else:
                print >>out, '   %s already installed' % product
        print >>out, 'Done\n'
        
def registerPolicy(context):
    addPolicy('Archetypes Site', ArchetypesSitePolicy())
