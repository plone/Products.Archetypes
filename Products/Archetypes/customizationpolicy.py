"""Archetypes customization policy for Plone sites

Based on the multilingual policy from Plone Solutions
"""

__author__  = 'Christian Heimes'
__docformat__ = 'restructuredtext'

from zope.component import getUtility
from StringIO import StringIO

from logging import getLogger
logger = getLogger('Archetypes')

try:
    import Products.CMFPlone
except ImportError:
    class DefaultCustomizationPolicy:
        pass
    def addPolicy(*args, **kwargs):
        raise ValueError('CustomizationPolicies not available.')
        
else:
    from Products.CMFPlone.Portal import addPolicy
    from Products.CMFPlone.CustomizationPolicy import DefaultCustomizationPolicy

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.utils import shasattr

HAS_PLONE21 = True

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
    if not HAS_PLONE21:
        addPolicy('Archetypes Site', ArchetypesSitePolicy())
