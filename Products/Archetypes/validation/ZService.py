from Products.Archetypes.validation.interfaces.IValidationService import IValidationService
from Products.Archetypes.validation.service import Service

from Acquisition import Implicit
from Globals import InitializeClass
from AccessControl import ClassSecurityInfo

from AccessControl import ModuleSecurityInfo

# make validator service public
security = ModuleSecurityInfo('Products.Archetypes.validation.config')
security.declarePublic('validation')

class ZService(Service, Implicit):
    """Service running in a zope site - exposes some methods""" 

    security = ClassSecurityInfo()
    __implements__ = IValidationService

    security.declarePublic('validate')
    security.declarePublic('__call__')
    security.declarePublic('validatorFor')

InitializeClass(ZService) 
