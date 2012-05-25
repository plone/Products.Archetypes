"""Interfaces for validation subscription adapters. Provide one of these to
perform pre- and post- validation on save.

If you're not familiar with subscription adapters, see zope.component's
README.txt and interfaces.py.
"""

from zope.interface import Interface


class IObjectValidation(Interface):
    """Pre- or post-validate an Archetypes object (common base interface)

    Will be called as a subscription adapter during validation.
    """

    def __call__(request):
        """Validate the context object. Return a dict with keys of fieldnames
        and values of error strings.
        """


class IObjectPreValidation(IObjectValidation):
    """Validate before schema validation
    """


class IObjectPostValidation(IObjectValidation):
    """Validate after schema validation
    """
