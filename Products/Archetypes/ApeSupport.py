# Bring generic Ape Support to Archetypes
# The goal of this module is to implement
# generic mapping of Archetypes Schema
# to real tables with real columns for
# each field in the schema
# **Experimental**

#  Whats working so far:
#  The following types are handled so far:
#  - string,int

#  Whats not working so far:

#  - References,images are not yet supported
#  - Renaming of objects generates errors

#  ArchGenXML has support for APE:
#  when you invoke ArchGenXML with the option --ape-support
#  the outline_od.xmi sample works with APE correctly
#  all ape_config and the serializer/gateway stuff is generated for you


from AccessControl import ClassSecurityInfo
from Products.Archetypes.BaseUnit import BaseUnit
from Products.Archetypes.public import *
from types import InstanceType,ClassType

from apelib.core.interfaces import IGateway, ISerializer
from apelib.sql.sqlbase import SQLGatewayBase
from apelib.sql.structure import RowSequenceSchema
from apelib.zodb3.serializers import RemainingState as RemainingBase


from apelib.core.interfaces \
     import ISerializer, IFullSerializationEvent, IFullDeserializationEvent
from Persistence import Persistent, PersistentMapping
from StringIO import StringIO
from cPickle import Pickler, Unpickler, UnpickleableError
import os


#map types between APE and Archetypes Schemas

typemap={
    'text':'string',
    'datetime':'string',
    'boolean':'int',
    #'reference':'string:list',
    'computed':'string' #ouch!!
}

def AtType2ApeType(f):
    t=f._properties['type']
    if t=='reference':
        #print 'REF:',f.getName(),f.multiValued
        if f.multiValued:
            return 'string'
        else:
            return 'string'
    if t=='computed':
        return None

    return typemap.get(t,t)

def AtSchema2ApeSchema(atschema):
    schema=RowSequenceSchema()
    column_defs=[]
    for f in atschema.fields():
        if f.isMetadata:
            continue
        pk=0
        name = f.getName()
        t = AtType2ApeType(f)
        if not t: # then dont add it to the schema
            continue
        if name=='id':pk=1
        schema.addField(name, t,pk)
        column_defs.append((name,t,pk))

    #print schema,tuple(column_defs)
    return schema,tuple(column_defs)

# creates a generic gateway instance based on
# the klass's Schema
def constructGateway(klass):
    res=ArcheSQLGateway()
    res.klass=klass
    res.schema,res.column_defs=AtSchema2ApeSchema(klass.schema)
    res.table_base_name = klass.__name__.lower()
    return res

# creates a generic serializer instance based on
# the klass's Schema
def constructSerializer(klass):
    res=ArcheSerializer()
    res.klass=klass
    res.schema=AtSchema2ApeSchema(klass.schema)[0]
    return res

# generic Gateway class.
# which reflects the class's Schema
class ArcheSQLGateway (SQLGatewayBase):
    """SQL folder items gateway"""

    __implements__ = SQLGatewayBase.__implements__

    def getSchema(self):
        return self.schema

    def load(self, event):
        print 'ArcheGateway::load : ',self.klass.__name__,event.getKey()
        key = long(event.getKey())
        items = self.execute(event, 'read', 1, key=key)
        if items:
            state = []
            for i in range(0,len(self.column_defs)):
                cd=self.column_defs[i]
                s=(cd[0],cd[1],items[0][i])
                state.append(s)
        else:
            state = ''
        state=tuple(state)
        return state,state

    def store(self, event, state):
        print 'ArcheGateway::store : ',self.klass.__name__,event.getKey()
        key = long(event.getKey())
        items = self.execute(event, 'read', 1, key=key)
        col_name = self.column_defs[0][0]
        conn = event.getConnection(self.conn_name)
        kw = {'key': key, }
        for s in state:
            kw[s[0]]=s[2]

        if items:
            # update.
            self.execute(event, 'update', **kw)
        else:
            # insert.
            self.execute(event, 'insert', **kw)
        return tuple(state)


# generic Serializer class
# which reflects the class's Schema
class ArcheSerializer:
    """Serializer for OFS.PropertyManager properties."""

    __implements__ = ISerializer

    schema = RowSequenceSchema()

    def getSchema(self):
        return self.schema

    def canSerialize(self, object):
        return isinstance(object, Master)

    def serialize(self, object, event):
        res = []
        for f in object.Schema().fields():
            if f.isMetadata:
                continue

            name = f.getName()
            t = AtType2ApeType(f)
            if not t:
                continue
            event.ignoreAttribute(name)
            data = f.getAccessor(object)()
            res.append((name, t, data))
            event.notifySerialized(name, getattr(object,name), 1)
        return tuple(res)

    def deserialize(self, object, event, state):
        for id, t, v in state:
            object.__dict__.update({id:v})

# this replacement of RemainingState is necessary in order to
# replace the BaseUnit members by string data because
# Baseunits are not pickleable (dunno why)
# overloaded the serialize method in order to clean the __dict__
# correctly
class RemainingState(RemainingBase):

    def cleanDictCopy(self,dict):
        ''' cleans out the baseUnit instances of the dict, because the are not picklable '''
        res={}

        for k in dict.keys():
            v=dict[k]
            if type(v) == type({}) or ec_isinstance(v,PersistentMapping):
                v1=self.cleanDictCopy(v)
            elif ec_isinstance(v,BaseUnit):
                v1=v.getRaw()
            else:
                v1=v
            res[k]=v1

        return res

    def serialize(self, object, event):
        assert IFullSerializationEvent.isImplementedBy(event)
        assert isinstance(object, Persistent)

        # Allow pickling of cyclic references to the object.
        event.notifySerialized('self', object, 0)

        # Ignore previously serialized attributes
        state = self.cleanDictCopy(object.__dict__)

        for key in state.keys():
            if key.startswith('_v_'):
                del state[key]
        for attrname in event.getSerializedAttributeNames():
            if state.has_key(attrname):
                del state[attrname]
        if not state:
            # No data needs to be stored
            return ''

        outfile = StringIO()
        p = Pickler(outfile)
        unmanaged = []

        def persistent_id(ob, getInternalRef=event.getInternalRef,
                          unmanaged=unmanaged):
            ref = getInternalRef(ob)
            if ref is None:
                if hasattr(ob, '_p_oid'):
                    # Persistent objects that end up in the remainder
                    # are unmanaged.  Tell ZODB about them so that
                    # ZODB can deal with them specially.
                    unmanaged.append(ob)
            return ref

        p.persistent_id = persistent_id
        try:
            p.dump(state)
        except UnpickleableError, exc:
            # Try to reveal which attribute is unpickleable.
            attrname = None
            attrvalue = None
            for key, value in state.items():
                del unmanaged[:]
                outfile.seek(0)
                outfile.truncate()
                p = Pickler(outfile)
                p.persistent_id = persistent_id
                try:
                    p.dump(value)
                except UnpickleableError:
                    attrname = key
                    attrvalue = value
                    break
            if attrname is not None:
                # Provide a more informative exception.
                if os.environ.get('APE_TRACE_UNPICKLEABLE'):
                    # Provide an opportunity to examine
                    # the "attrvalue" attribute.
                    import pdb
                    pdb.set_trace()
                raise RuntimeError(
                    'Unable to pickle the %s attribute, %s, '
                    'of %s at %s.  %s.' % (
                    repr(attrname), repr(attrvalue), repr(object),
                    repr(event.getKeychain()), str(exc)))
            else:
                # Couldn't help.
                raise

        p.dump(unmanaged)
        s = outfile.getvalue()
        event.addUnmanagedPersistentObjects(unmanaged)
        return s

# helper functions for issubclass and isinstance
# with extension classes.
# borrowed from Greg Ward (thanx Greg :)
def ec_issubclass (class1, class2):
    """A version of 'issubclass' that works with extension classes
    as well as regular Python classes.
    """

    # Both class objects are regular Python classes, so use the
    # built-in 'issubclass()'.
    if type(class1) is ClassType and type(class2) is ClassType:
        return __builtin__.issubclass(class1, class2)

    # Both so-called class objects have a '__bases__' attribute: ie.,
    # they aren't regular Python classes, but they sure look like them.
    # Assume they are extension classes and reimplement what the builtin
    # 'issubclass()' does behind the scenes.
    elif hasattr(class1, '__bases__') and hasattr(class2, '__bases__'):
        # XXX it appears that "ec.__class__ is type(ec)" for an
        # extension class 'ec': could we/should we use this as an
        # additional check for extension classes?

        # Breadth-first traversal of class1's superclass tree.  Order
        # doesn't matter because we're just looking for a "yes/no"
        # answer from the tree; if we were trying to resolve a name,
        # order would be important!
        stack = [class1]
        while stack:
            if stack[0] is class2:
                return 1
            stack.extend(list(stack[0].__bases__))
            del stack[0]
        else:
            return 0

    # Not a regular class, not an extension class: blow up for consistency
    # with builtin 'issubclass()"
    else:
        raise TypeError, "arguments must be class or ExtensionClass objects"

# ec_issubclass ()

def ec_isinstance (object, klass):
    """A version of 'isinstance' that works with extension classes
    as well as regular Python classes."""

    if type(klass) is ClassType:
        return isinstance(object, klass)
    elif hasattr(object, '__class__'):
        return ec_issubclass(object.__class__, klass)
    else:
        return 0
