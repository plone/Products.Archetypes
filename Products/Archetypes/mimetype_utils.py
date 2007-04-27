from zope.component import getUtility
from Products.CMFCore.interfaces import IPropertiesTool
from Products.PortalTransforms.interfaces import IPortalTransformsTool

#
# default- and allowable content type handling
#

def getDefaultContentType(context):
    portal_properties = getUtility(IPropertiesTool)
    site_properties = getattr(portal_properties, 'site_properties', None)
    return site_properties.getProperty('default_contenttype')

def setDefaultContentType(context, value):
    portal_properties = getUtility(IPropertiesTool)
    site_properties = portal_properties.site_properties
    site_properties.manage_changeProperties(default_contenttype=value)
        
def getAllowedContentTypes(context):
    """ computes the list of allowed content types by subtracting the site property blacklist 
        from the list of installed types.
    """
    allowable_types = getAllowableContentTypes(context)
    forbidden_types = getForbiddenContentTypes(context)
    allowed_types = [type for type in allowable_types if type not in forbidden_types]
    return allowed_types
    
def getAllowableContentTypes(context):
    """ retrieves the list of installed content types by querying portal transforms. """
    portal_transforms = getUtility(IPortalTransformsTool)
    return portal_transforms.listAvailableTextInputs()

def setForbiddenContentTypes(context, forbidden_contenttypes=[]):
    """ Convenience method for settng the site property 'forbidden_contenttypes'."""
    portal_properties = getUtility(IPropertiesTool)
    site_properties = portal_properties.site_properties
    site_properties.manage_changeProperties(forbidden_contenttypes=tuple(forbidden_contenttypes))

def getForbiddenContentTypes(context):
    """ Convenence method for retrevng the site property 'forbidden_contenttypes'."""
    portal_properties = getUtility(IPropertiesTool)
    site_properties = portal_properties.site_properties
    if site_properties.hasProperty('forbidden_contenttypes'):
        return list(site_properties.getProperty('forbidden_contenttypes'))
    else:
        return []
