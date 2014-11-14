"""Default- and allowable content type handling.
"""
from Products.CMFCore.utils import getToolByName

try:
    from Products.CMFPlone.interfaces import IMarkupSchema
    from plone.registry.interfaces import IRegistry
    from zope.component import getUtility
    from zope.component.interfaces import ComponentLookupError
except ImportError:
    IMarkupSchema = None


def markupRegistrySettings(context):
    if not IMarkupSchema:
        return None
    try:
        # get the new registry
        registry = getUtility(IRegistry, context=context)
        settings = registry.forInterface(
            IMarkupSchema,
            prefix='plone',
        )
    except (KeyError, ComponentLookupError):
        settings = None
    return settings


def getDefaultContentType(context):
    default_type = 'text/plain'
    reg = markupRegistrySettings(context)
    if reg:
        default_type = reg.default_type
    else:
        portal_props = getToolByName(context, 'portal_properties', None)
        if portal_props is not None:
            site_props = getattr(portal_props, 'site_properties', None)
            if site_props is not None:
                default_type = site_props.getProperty('default_contenttype')
    return default_type


def setDefaultContentType(context, value):
    portal_properties = getToolByName(context, 'portal_properties', None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
            site_properties.manage_changeProperties(default_contenttype=value)


def getAllowedContentTypes(context):
    """Computes the list of allowed content types by subtracting the site
    property blacklist from the list of installed types.
    """
    allowed_types = []
    reg = markupRegistrySettings(context)
    if reg:
        allowed_types = reg.allowed_types
    else:
        allowable_types = getAllowableContentTypes(context)
        forbidden_types = getForbiddenContentTypes(context)
        allowed_types = [
            _type for _type in allowable_types if _type not in forbidden_types]
    return allowed_types


def getAllowableContentTypes(context):
    """Retrieves the list of installed content types by querying portal
    transforms.
    """
    portal_transforms = getToolByName(context, 'portal_transforms')
    return portal_transforms.listAvailableTextInputs()


def setForbiddenContentTypes(context, forbidden_contenttypes=None):
    """Convenience method for settng the site property
    ``forbidden_contenttypes``.
    """
    if forbidden_contenttypes is None:
        forbidden_contenttypes = []
    portal_properties = getToolByName(context, 'portal_properties', None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
            site_properties.manage_changeProperties(
                forbidden_contenttypes=tuple(forbidden_contenttypes))


def getForbiddenContentTypes(context):
    """Convenence method for retrevng the site property
    ``forbidden_contenttypes``.
    """
    portal_properties = getToolByName(context, 'portal_properties', None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
            if site_properties.hasProperty('forbidden_contenttypes'):
                return list(
                    site_properties.getProperty('forbidden_contenttypes'))
    return []
