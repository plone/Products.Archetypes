import ZODB
from ZODB.PersistentMapping import PersistentMapping
from Products.CMFCore.utils import getToolByName
from debug import log, log_exc
from ExtensionClass import Base

class ReferenceEngine(Base):
    def __init__(self):
        self.refs = PersistentMapping()
        self.bref = PersistentMapping()

    def getRefs(self, object):
        refs = []
        try:
            if type(object) != type(''):
                object = object.UID()
            refs = self.refs.get(object, [])
        except AttributeError:
            pass
        
        return refs

    def getBRefs(self, object):
        brefs = []
        try:
            if type(object) != type(''):
                object = object.UID()        
            brefs = self.bref.get(object, [])
        except AttributeError:
            pass
        return brefs
    
    def addReference(self, object, target):
        if type(object) != type(''):
            oid = object.UID()
        else:
            oid = object

        if type(target) != type(''):
            tid = target.UID()
        else:
            tid = target

        refs = self.refs.get(oid, [])
            
        if tid not in refs:
            self._addRef(oid, tid, refs=refs)
            self._addBref(oid, tid)

    def assertId(self, uid):
        catalog = getToolByName(self, 'portal_catalog')
        result  = catalog({'UID' : uid})
        if result:
            return 1
        return 0

    def _addRef(self, object, target, refs=None):
        if not refs:
            refs = self.refs.get(object, [])

        if target in refs:
            return

        if self.assertId(target):
            refs.insert(0, target)
            self.refs[object] = refs

    def _addBref(self, object, target):
        brefs = self.bref.get(target, [])
        brefs.insert(0, object)
        self.bref[target] = brefs


    def _delRef(self, object, target):
        refs = self.refs.get(object, [])
        try:
            refs.remove(target)
            self.refs[object] = refs
        except ValueError:
            pass
        

    def _delBref(self, object, target):
        brefs = self.bref.get(object, [])
        try:
            brefs.remove(target)
            self.bref[object] = brefs
        except ValueError:
            pass
        
    def _delReferences(self, object):
        ##TODO: remove empty ref/bref entries after delete
        #Delete all back refs and all refs
        if type(object) != type(''):
            oid = object.UID()
        else:
            oid = object
            
        brefs = list(self.bref.get(oid, []))
        for b in brefs:
            # For each backref delete this object from its
            # ref list and then remove it from the back ref list
            #log("del bref %s" % (b))
            self._delRef(b, oid)
            self._delBref(oid, b)
            
        refs = list(self.refs.get(oid, []))
        for r in refs:
            self._delRef(oid, r)
            self._delBref(r, oid)


    def deleteReferences(self, object):
        """remove all reference to and from object"""
        self._delReferences(object)
            

    def deleteReference(self, object, target):
        """Remove a single ref/backref pair from an object"""
        if type(object) != type(''):
            oid = object.UID()
        else:
            oid = object
            
        if type(target) != type(''):
            tid = target.UID()
        else:
            tid = target

        self._delRef(oid, tid)
        self._delBref(tid, oid)
        
