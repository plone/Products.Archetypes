
from Acquisition import aq_base

from Products.Archetypes.Storage import Storage
from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.Registry import registerStorage


class SessionStorage(Storage):
    """Stores data in a session."""

    __implements__ = IStorage

    _v_session_data=None

    def get(self, name, instance, **kwargs):
        session_data=self.getSessionData(instance)
        if session_data:
            ns=self.getNS(instance)
            nsc=session_data.get(ns, {})
            if nsc.has_key(name):
                return nsc.get(name)
        raise AttributeError(name)

    def set(self, name, instance, value, **kwargs):
        session_data=self.getSessionData(instance)
        if session_data:
            ns=self.getNS(instance)
            nsc=session_data.get(ns, {})
            value = aq_base(value)
            nsc[name]=value
            session_data.set(ns, nsc)

    def unset(self, name, instance, **kwargs):
        session_data=self.getSessionData(instance)
        if session_data:
            ns=self.getNS(instance)
            nsc=session_data.get(ns, {})
            try:
                if nsc.has_key(name):
                    del nsc[name]
            except:
                pass

    def getSessionData(self, instance):
        #Violates encapsulation of instance by setting private attribute _v_session_data
        #(but it saves a hole lot of calls to getSessionData if the storage is used
        # by several fields :-)
        #
        if hasattr(instance, '_v_session_data'): return instance._v_session_data
        session = getattr( instance, 'session_data_manager', None )
        if session:
            instance._v_session_data=session.getSessionData()
        return instance._v_session_data


    def getNS(self, instance):
        return '/'.join(instance.getPhysicalPath())





registerStorage(SessionStorage)
