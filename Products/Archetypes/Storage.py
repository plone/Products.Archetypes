import ZODB
from ZODB.PersistentMapping import PersistentMapping
from Products.CMFCore.utils import getToolByName
from SQLMethod import SQLMethod
from interfaces.storage import IStorage, ISQLStorage
from interfaces.field import IObjectField
from interfaces.layer import ILayer
from exceptions import SQLInitException
from debug import log
from config import TOOL_NAME

type_map = {'text':'string',
            'datetime':'date',
            'lines':'lines',
            'integer':'int'
            }

sql_type_map = {'integer':'int'}

class Storage:
    __implements__ = IStorage

    def getName(self):
        return self.__class__.__name__

    def get(self, name, instance, **kwargs):
        raise NotImplementedError('%s: get' % self.getName())

    def set(self, name, instance, value, **kwargs):
        raise NotImplementedError('%s: set' % self.getName())

    def unset(self, name, instance, **kwargs):
        raise NotImplementedError('%s: unset' % self.getName())

class StorageLayer(Storage):
    __implements__ = (IStorage, ILayer)

    def initalizeInstance(self, instance):
        raise NotImplementedError('%s: initalizeInstance' % self.getName())

    def cleanupInstance(self, instance):
        raise NotImplementedError('%s: cleanupInstance' % self.getName())

    def initalizeField(self, instance, field):
        raise NotImplementedError('%s: initalizeField' % self.getName())

    def cleanupField(self, instance, field):
        raise NotImplementedError('%s: cleanupField' % self.getName())
    
class AttributeStorage(Storage):
    __implements__ = IStorage

    def get(self, name, instance, **kwargs):
        return getattr(instance, name)

    def set(self, name, instance, value, **kwargs):
        setattr(instance, name, value)
        instance._p_changed = 1

    def unset(self, name, instance, **kwargs):
        try:
            delattr(instance, name)
        except AttributeError:
            pass
        instance._p_changed = 1

class ObjectManagedStorage(Storage):
    __implements__ = IStorage
    
    def get(self, name, instance, **kwargs):
        return instance._getOb(name)

    def set(self, name, instance, value, **kwargs):
        instance._setObject(name, value)
        instance._p_changed = 1

    def unset(self, name, instance, **kwargs):
        instance._delObject(name)
        instance._p_changed = 1

class MetadataStorage(StorageLayer):
    __implements__ = (IStorage, ILayer)
    
    def initalizeInstance(self, instance):
        if not hasattr(instance, "_md"):
            instance._md = PersistentMapping()
            instance._p_changed = 1

            
    def initalizeField(self, instance, field):
        pass

    def get(self, name, instance, **kwargs):
        try:
            value = instance._md[name]
        except KeyError, msg:
            # We are acting like an attribute, so
            # raise AttributeError instead of KeyError
            raise AttributeError(name, msg)
        return value

    def set(self, name, instance, value, **kwargs):
        instance._md[name] = value
        instance._p_changed = 1
        
    def unset(self, name, instance, **kwargs):
        if not hasattr(instance, "_md"):
            log("Broken instance %s, no _md" % instance)
        else:
            del instance._md[name]
            instance._p_changed = 1

    def cleanupField(self, instance, field, **kwargs):
        self.unset(field.name, instance)

    def cleanupInstance(self, instance):
        del instance._md

class MySQLStorage(StorageLayer):
    __implements__ = (ISQLStorage, ILayer)
    
    def initalizeInstance(self, instance):
        c_tool = getToolByName(instance, TOOL_NAME)
        connection_id = c_tool.getConnFor(instance)
        fields = instance.type.fields()
        fields = [f for f in fields if IObjectField.isImplementedBy(f) \
                  and ISQLStorage.isImplementedBy(f.getStorage())]
        columns = []
        args = {}
        for field in fields:
            type = field.type
            name = field.name
            default = field.default
            column = '%s %s' % (name, type)
            if default is not None:
                if type == 'text':
                    default = "'%s'" % default
                column = "%s not null default %s" % (column, default)
            columns.append(column)
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        args['columns'] = ', ' + ', '.join(columns)
        # print args['columns']
        query = """create table <dtml-var table> \
                   (UID char(50) primary key not null<dtml-var columns>)"""
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), query)
        try:
            query, result = method(test__=1, **args)
            # print query
        except Exception, msg:
            # usually, table already exists
            # raise SQLInitException(msg)
            pass

        query = """insert into <dtml-var table> \
                   set UID=<dtml-sqlvar UID type="string">"""
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), query)
        try:
            query, result = method(test__=1, **args)
            # print query
        except Exception, msg:
            # usually, duplicate key
            # raise SQLInitException(msg)
            pass

    def get(self, name, instance, **kwargs):
        c_tool = getToolByName(instance, TOOL_NAME)
        connection_id = c_tool.getConnFor(instance)
        field = instance.getField(name)
        default = field.default
        args = {}
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        args['field'] = name
        query = """select <dtml-var field> from <dtml-var table> \
                   where <dtml-sqltest UID op="eq" type="string">"""
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), query)
        try:
            query, result = method(test__=1, **args)
            result = result[0][0]
        except Exception, msg:
            raise AttributeError(msg)
        return result

    def set(self, name, instance, value, **kwargs):
        c_tool = getToolByName(instance, TOOL_NAME)
        connection_id = c_tool.getConnFor(instance)
        field = instance.getField(name)
        type = type_map.get(field.type, 'string')
        sql_type = sql_type_map.get(field.type, 'string')
        default = field.default
        args = {}
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        field_name = '%s:%s' % (name, type)
        if default:
            if type == 'string':
                default = "'%s'" % default
            field_name =  "%s=%s" % (args['field'], default)
        args[field_name] = name
        args['field'] = name
        args['value'] = value
        query = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s"> \
                   where  <dtml-sqltest UID op="eq" type="string">""" % sql_type
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), query)
        query, result = method(test__=1, **args)
        
    def unset(self, name, instance, **kwargs):
        # probably use drop column here
        pass

    cleanupField = unset
    
    def cleanupInstance(self, instance):
        # the object is being deleted. remove data from sql.
        c_tool = getToolByName(instance, TOOL_NAME)
        connection_id = c_tool.getConnFor(instance)
        args = {}
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        query = """delete from <dtml-var table> \
        where <dtml-sqltest UID op="eq" type="string">"""
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), query)
        try:
            query, result = method(test__=1, **args)
        except Exception, msg:
            # dunno what could happen here
            # raise SQLCleanupException(msg)
            pass
