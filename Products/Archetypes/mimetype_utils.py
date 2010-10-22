from Products.CMFCore.utils import getToolByName

#
# default- and allowable content type handling
#

def getDefaultContentType(context):
    portal_properties = getToolByName(context, 'portal_properties', None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
            return site_properties.getProperty('default_contenttype')
    return 'text/plain'

def setDefaultContentType(context, value):
    portal_properties = getToolByName(context, 'portal_properties', None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
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
    portal_transforms = getToolByName(context, 'portal_transforms')
    return portal_transforms.listAvailableTextInputs()

def setForbiddenContentTypes(context, forbidden_contenttypes=[]):
    """ Convenience method for settng the site property 'forbidden_contenttypes'."""
    portal_properties = getToolByName(context, 'portal_properties', None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
            site_properties.manage_changeProperties(forbidden_contenttypes=tuple(forbidden_contenttypes))

def getForbiddenContentTypes(context):
    """ Convenence method for retrevng the site property 'forbidden_contenttypes'."""
    portal_properties = getToolByName(context, 'portal_properties', None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
            if site_properties.hasProperty('forbidden_contenttypes'):
                return list(site_properties.getProperty('forbidden_contenttypes'))
    return []
