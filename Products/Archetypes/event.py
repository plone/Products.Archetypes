"""Event definitions
"""

from zope.app.event.objectevent import ObjectEvent
from zope.interface import implements

from Products.Archetypes.interfaces import IObjectPreValidatingEvent
from Products.Archetypes.interfaces import IObjectPostValidatingEvent

class ObjectPreValidatingEvent(ObjectEvent):
    """An Archetypes object is being pre-validated.
    """
    
    implements(IObjectPreValidatingEvent)
    
    def __init__(self, object, REQUEST, errors):
        super(ObjectPreValidatingEvent, self).__init__(object) 
        self.REQUEST = REQUEST
        self.errors = errors

class ObjectPostValidatingEvent(ObjectEvent):
    """An archetypes object is being post-validated.
    """
    
    implements(IObjectPostValidatingEvent)
    
    def __init__(self, object, REQUEST, errors):
        super(ObjectPostValidatingEvent, self).__init__(object) 
        self.REQUEST = REQUEST
        self.errors = errors