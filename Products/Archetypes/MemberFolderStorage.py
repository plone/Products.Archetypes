
from Acquisition import aq_base
from AccessControl import getSecurityManager
from Products.Archetypes.interfaces.storage import IStorage
from Products.Archetypes.Registry import registerStorage
from Products.Archetypes.utils import capitalize
from Products.Archetypes.SessionStorage import SessionStorage

def renderMethodName(typeofname, name):
    name = capitalize(name)
    return typeofname+name


class ContainerFactory:
    """\
    A object that help create new objects in a parent container.
    It can also hole referense to one sub ContainerFactory and calls
    it when the folder is built.
    """

    __sub_container_=None

    def __init__(self, container_id, container_class, *args, **kwargs):
        """\
        Enter object id, object class and additional args and
        kwargs.
        """
        self.container_id=container_id
        self.container_class=container_class
        self.args=args
        self.kwargs=kwargs

    def add(self, sub_container):
        self.__sub_container_=sub_container

    def build(self, parent):
        obj=parent
        if hasattr(aq_base(parent), self.container_id ):
            obj=getattr(parent, self.container_id)
        else:
            obj=self.container_class(self.container_id, *self.args, **self.kwargs)
            parent._setObject(self.container_id, obj)
            obj=getattr(parent, self.container_id)
        if self.__sub_container_ is not None:
            obj=self.__sub_container_.build(obj)
        return obj


class MemberFolderStorage(SessionStorage):
    """Stores data in a MemberFolder or in a Session if the user doesn't have a MemberFolder."""

    __implements__ = IStorage

    def __init__(self, use_containers=None, use_session=1, **kwargs):
        """\
        Can take a ContainerFactory structure that will create a
        structure of object in the Members HomeFolder. The data is saved
        in the bottom of the structure. If the structure exists the
        object is only traversed.

        use_session=1, by default data is saved in a session if the
        members HomeFolder can't be retrieved. If use_session=0 sessions
        will not be use and any changes to the value will be silently
        forgotten (using the fields default instead).
        """
        self.use_containers=use_containers
        self.use_session=use_session

    def get(self, name, instance, **kwargs):
        mf=self.getStorageObject(instance)
        if mf:
            method_name=renderMethodName('get', name)
            if hasattr(aq_base(mf), method_name):
                method=getattr(mf, method_name)
                if callable(method):
                    return method()
            if not hasattr(aq_base(mf), name):
                raise AttributeError(name)
            return getattr(mf, name)
        elif self.use_session:
            return SessionStorage.get(self, name, instance, **kwargs)

    def set(self, name, instance, value, **kwargs):
        # Remove acquisition wrappers
        mf=self.getStorageObject(instance)
        if mf:
            value = aq_base(value)
            method_name=renderMethodName('set', name)
            if hasattr(aq_base(mf), method_name):
                method=getattr(mf, method_name)
                if callable(method):
                    return method(value)
            else:
                setattr(aq_base(mf), name, value)
                mf._p_changed = 1
        elif self.use_session:
            return SessionStorage.set(self, name, instance, value, **kwargs)


    def unset(self, name, instance, **kwargs):
        mf=self.getStorageObject(instance)
        if mf:
            try:
                method_name=renderMethodName('del', name)
                if hasattr(aq_base(mf), method_name):
                    method=getattr(mf, method_name)
                    if callable(method):
                        return method()
                else:
                    delattr(aq_base(mf), name)
            except AttributeError:
                pass
            mf._p_changed = 1
        elif self.use_session:
            return SessionStorage.unset(self, name, instance, **kwargs)


    def getStorageObject(self, instance):
        mf = instance.portal_membership.getHomeFolder()
        if mf and self.use_containers is not None:
            mf=self.use_containers.build(mf)
        return mf



registerStorage(MemberFolderStorage)
