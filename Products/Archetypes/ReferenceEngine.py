import ZODB
from ZODB.PersistentMapping import PersistentMapping
from Products.CMFCore.utils import getToolByName
from debug import log, log_exc
from ExtensionClass import Base

from interfaces.referenceable import IReferenceable
from utils import unique
from types import StringType
from config import UID_CATALOG

class ReferenceEngine(Base):
    def __init__(self):
        self.refs = PersistentMapping()
        self.bref = PersistentMapping()


    def hasRelationshipTo(self, object, target, relationship=None):
        if type(target) != StringType:
            target = target.UID()
        refs = self.getRefs(object, relationship)
        return target in refs

    def getRefs(self, object, relationship=None):
        refs = []
        try:
            if type(object) != StringType:
                object = object.UID()
            refs = self.refs.get(object, [])
        except AttributeError:
            pass

        refs = [r for r,grp in refs if not relationship or (relationship and (grp == relationship))]
        return refs

    def getBRefs(self, object, relationship=None):
        brefs = []
        try:
            if type(object) != StringType:
                object = object.UID()
            brefs = self.bref.get(object, [])
        except AttributeError:
            pass

        brefs = [r for r,grp in brefs if not relationship or (relationship and (grp == relationship))]
        return brefs

    def addReference(self, object, target, relationship=None):
        """The beforeAddReference hook will be called on the target with
        the object attempting to add the reference. An exception will
        prevent the references from being added.
        """

        if type(object) != StringType:
            oid = object.UID()
        else:
            oid = object

        if type(target) != StringType:
            tid = target.UID()
        else:
            tid = target

        refs = self.refs.get(oid, [])


        add_hook = getattr(target, 'beforeAddReference', None)
        if add_hook and callable(add_hook):
            try:
                add_hook(object, relationship)
            except:
                return

        if tid not in refs:
            self._addRef(oid, tid, refs=refs, relationship=relationship)
            self._addBref(oid, tid, relationship=relationship)

    def assertId(self, uid):
        catalog = getToolByName(self, UID_CATALOG)
        result  = catalog({'UID' : uid})
        if result:
            return 1
        return 0

    def _addRef(self, object, target, refs=None, relationship=None):
        if not refs:
            refs = self.refs.get(object, [])

        key = (target, relationship)
        if key in refs:
            return

        if self.assertId(target):
            refs.insert(0, key)
            self.refs[object] = refs


    def _addBref(self, object, target, relationship):
        key = (object, relationship)
        brefs = self.bref.get(target, [])
        if key in brefs:
            return
        brefs.insert(0, key)
        self.bref[target] = brefs

    def _delRef(self, object, target, relationship=None):
        refs = self.refs.get(object, [])

        #Scan for the target in the list and remove it
        if not relationship:
            for k, r in refs:
                if k == target:
                    refs.remove((k,r))
        else:
            refs.remove((target, relationship))

        self.refs[object] = refs


    def _delBref(self, object, target, relationship=None):
        brefs = list(self.bref.get(object, []))

        if not relationship:
            for k, r in brefs:
                if k == target:
                    brefs.remove((k,r))
        else:
            brefs.remove((target, relationship))

        self.bref[object] = brefs

    def _delReferences(self, object, relationship=None):
        #Delete all back refs and all refs
        if type(object) != StringType:
            oid = object.UID()
        else:
            oid = object

        #Everything that points at 'object'
        brefs = list(self.bref.get(oid, []))
        for b, rel in brefs:
            # For each backref delete this object from its
            # ref list and then remove it from the back ref list
            if not relationship or rel == relationship:
                self._delRef(b, oid)
                self._delBref(oid, b)

        #Every thing that 'object' points at
        refs = list(self.refs.get(oid, []))
        for r, rel in refs:
            if not relationship or rel == relationship:
                self._delRef(oid, r)
                self._delBref(r, oid)


    def deleteReferences(self, object, relationship=None):
        """remove all reference to and from object"""
        self._delReferences(object, relationship=relationship)


    def deleteReference(self, object, target, relationship=None):
        """Remove a single ref/backref pair from an object, the
        beforeDeleteReference hook will be called on the target, an
        exception will prevent the reference from being deleted
        """

        if type(object) != StringType:
            oid = object.UID()
        else:
            oid = object

        if type(target) != StringType:
            tid = target.UID()
        else:
            tid = target

        del_hook = getattr(target, 'beforeDeleteReference', None)
        if del_hook and callable(del_hook):
            try:
                del_hook(object, relationship)
            except:
                return


        self._delRef(oid, tid, relationship)
        self._delBref(tid, oid, relationship)

    def isReferenceable(self, object):
        return IReferenceable.isImplementedBy(object) or hasattr(object, 'isReferenceable')


    def getRelationships(self, object):
        refs = []
        try:
            if type(object) != StringType:
                object = object.UID()
            refs = self.refs.get(object, [])
        except AttributeError:
            pass

        refs = [grp for r,grp in refs]
        return unique(refs)

