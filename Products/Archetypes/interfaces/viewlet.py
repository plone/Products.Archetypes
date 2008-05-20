from zope.viewlet.interfaces import IViewletManager

class IEditAfterFieldsets(IViewletManager):
    """Viewlet manager for Archetypes' edit screen.

    You can use this manager to add extra markup after the fieldsets, but
    before the form control buttons.
    """
