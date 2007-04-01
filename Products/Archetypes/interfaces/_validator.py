"""Interfaces for validation subscription adapters. Provide one of these to
perform pre- and post- validation on save.

If you're not familiar with subscription adapters, see zope.component's
README.txt and interfaces.py.
"""
    
from zope.interface import Interface

class IObjectPreValidation(Interface):
    """Pre-validate an Archetypes object
    
    Will be called as a subscription adapter during validation.
    """
    
    def __call__(request, errors):
        """Validate the context object. Put any error messages,
        keyed on field name, in the errors dict.
        """
    
class IObjectPostValidation(Interface):
    """Post-validate an Archetypes object
    
    Will be called as a subscription adapter during validation.
    """
    
    def __call__(request, errors):
        """Validate the context object. Put any error messages,
        keyed on field name, in the errors dict.
        """