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


def _markupRegistrySettings(context):
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


def _getSiteProperties(context):
    portal_properties = getToolByName(context, 'portal_properties', None)
    if portal_properties is not None:
        site_properties = getattr(portal_properties, 'site_properties', None)
        if site_properties is not None:
            return site_properties
    return None


def getDefaultContentType(context):
    default_type = 'text/plain'
    reg = _markupRegistrySettings(context)
    if reg:
        default_type = reg.default_type
    else:
        site_properties = _getSiteProperties(context)
        if site_properties is not None:
            default_type = site_properties.getProperty('default_contenttype')
    return default_type


def setDefaultContentType(context, value):
    reg = _markupRegistrySettings(context)
    if reg:
        reg.default_type = value
    else:
        site_properties = _getSiteProperties(context)
        if site_properties is not None:
            site_properties.manage_changeProperties(default_contenttype=value)


def getAllowedContentTypes(context):
    """Computes the list of allowed content types by subtracting the site
    property blacklist from the list of installed types.
    """
    allowed_types = []
    reg = _markupRegistrySettings(context)
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


def getForbiddenContentTypes(context):
    """Convenence method for retrevng the site property
    ``forbidden_contenttypes``.
    """
    site_properties = _getSiteProperties(context)
    if site_properties is not None:
        if site_properties.hasProperty('forbidden_contenttypes'):
            return list(
                site_properties.getProperty('forbidden_contenttypes'))
    return []


def setForbiddenContentTypes(context, forbidden_contenttypes=None):
    """Convenience method for settng the site property
    ``forbidden_contenttypes``.
    """
    if forbidden_contenttypes is None:
        forbidden_contenttypes = []

    site_properties = _getSiteProperties(context)
    if site_properties is not None:
        site_properties.manage_changeProperties(
            forbidden_contenttypes=tuple(forbidden_contenttypes))
