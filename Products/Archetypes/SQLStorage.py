from Products.CMFCore.utils import getToolByName
from SQLMethod import SQLMethod
from interfaces.storage import IStorage, ISQLStorage
from interfaces.field import IObjectField
from interfaces.layer import ILayer
from debug import log
from config import TOOL_NAME
from Storage import *
from sys import exc_info

class BaseSQLStorage(StorageLayer):
    # SQLStorage that is more or less ISO SQL, should be usable as a base
    __implements__ = (ISQLStorage, ILayer)

    query_create = """create table <dtml-var table> \
                      (UID char(50) primary key not null <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> \
                      set UID=<dtml-sqlvar UID type="string">"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s" optional> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_drop = """drop table <dtml-var table>"""

    sqlm_type_map = {'integer':'int'}
    db_type_map = {'fixedpoint': 'integer'}

    def map_fixedpoint(self, field, value):
        __traceback_info__ = repr(value)
        template = '%%d%%0%dd' % field.precision
        return template % value
    
    def unmap_fixedpoint(self, field, value):
        __traceback_info__ = repr(value)
        split = 10 ** field.precision
        return (value / split), (value % split)

    def map_datetime(self, field, value):
        # we don't want to lose even 0.001 second
        return value.ISO()[:-2] + str(value.second())

    def table_exists(self, instance):
        raise NotImplemented

    def is_initialized(self, instance):
        try:
            return self.__class__.__name__ in instance.__initialized
        except AttributeError:
            return None

    def _query(self, instance, query, args):
        c_tool = getToolByName(instance, TOOL_NAME)
        connection_id = c_tool.getConnFor(instance)
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), query)
        query, result = method(test__=1, **args)
        return result
    
    def initalizeInstance(self, instance):
        if self.is_initialized(instance):
            # duh, we don't need to be initialized twice
            return
        fields = instance.Schema().fields()
        fields = [f for f in fields if IObjectField.isImplementedBy(f) \
                  and f.getStorage().__class__ is self.__class__]
        columns = []
        args = {}
        for field in fields:
            type = self.db_type_map.get(field.type, field.type)
            name = field.name
            columns.append('%s %s' % (name, type))
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        args['columns'] = ', ' + ', '.join(columns)

        if not self.table_exists(instance):
            self._query(instance, self.query_create, args)
            log('created table %s\n' % args['table'])

        try:
            self._query(instance, self.query_insert, args)
        except:
            # usually, duplicate key
            # raise SQLInitException(msg)
            pass
        try:
            instance.__initialized += (self.__class__.__name__,)
        except AttributeError:
            instance.__initialized = (self.__class__.__name__,)

    def get(self, name, instance, **kwargs):
        if not self.is_initialized(instance):
            # ignore all calls before we're initialized - some manage_afterAdd() methods
            # try to get and set fields and we can't allow that to break
            return None
        field = instance.getField(name)
        default = field.default
        args = {}
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        args['field'] = name
        result = self._query(instance, self.query_select, args)[0][0]
        mapper = getattr(self, 'unmap_' + field.type, None)
        if mapper is not None:
            result = mapper(field, result)
        return result

    def set(self, name, instance, value, **kwargs):
        if not self.is_initialized(instance):
            # ignore all calls before we're initialized - some manage_afterAdd() methods
            # try to get and set fields and we can't allow that to break
            return None
        field = instance.getField(name)
        mapper = getattr(self, 'map_' + field.type, None)
        if mapper is not None:
            value = mapper(field, value)
        type = type_map.get(field.type, 'string')
        sql_type = self.sqlm_type_map.get(field.type, 'string')
        default = field.default
        args = {}
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        field_name = '%s:%s' % (name, type)
        if default:
            if type == 'string':
                default = "'%s'" % default
            field_name =  "%s=%s" % (name, default)
        args[field_name] = name
        args['field'] = name
        if value is not None:
            # omiting it causes dtml-sqlvar to insert NULL
            args['value'] = value
        self._query(instance, self.query_update % sql_type, args)
        
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
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), self.query_delete)
        try:
            query, result = method(test__=1, **args)
        except:
            # dunno what could happen here
            # raise SQLCleanupException(msg)
            pass

    def initalizeField(self, instance, field):
        pass

    def cleanupField(self, instance, field):
        pass

class GadflySQLStorage(BaseSQLStorage):
    __implements__ = BaseSQLStorage.__implements__

    query_create = """create table <dtml-var table> \
                      (UID varchar <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> \
                      set UID=<dtml-sqlvar UID type="string">"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s" optional> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_drop   = """drop table <dtml-var table>"""

    sqlm_type_map = {'integer':'int'}
    db_type_map = {'text': 'varchar',
                   'object': 'varchar',
                   'string': 'varchar'}


class MySQLSQLStorage(BaseSQLStorage):
    __implements__ = BaseSQLStorage.__implements__

    query_create = """create table <dtml-var table> \
                      (UID char(50) primary key not null <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> \
                      set UID=<dtml-sqlvar UID type="string">"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s" optional> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_drop   = """drop table <dtml-var table>"""

    sqlm_type_map = {'integer':'int'}
    db_type_map = {
        'object': 'text',
        'fixedpoint': 'float',
        'reference': 'text',
        'datetime': 'datetime',
        'string': 'text',
        }

    def table_exists(self, instance):
        result =  [r[0].lower() for r in self._query(instance, '''show tables''', {})]
        return instance.portal_type.lower() in result

class OracleSQLStorage(BaseSQLStorage):
    __implements__ = BaseSQLStorage.__implements__

    query_create = """create table <dtml-var table> \
                      (UID char(50) primary key not null <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> \
                      set UID=<dtml-sqlvar UID type="string">"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s" optional> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_drop   = """drop table <dtml-var table>"""

    sqlm_type_map = {'integer':'int'}
    db_type_map = {}
    

class PostgreSQLStorage(BaseSQLStorage):
    __implements__ = BaseSQLStorage.__implements__

    query_create = """create table <dtml-var table> \
                      (UID text primary key not null <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> (UID) values\
                      (<dtml-sqlvar UID type="string">)"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s" optional> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_drop   = """drop table <dtml-var table>"""

    sqlm_type_map = {'integer': 'int'}
    db_type_map = {
        'object': 'bytea',
        'fixedpoint': 'integer',
        'reference': 'text',
        'datetime': 'timestamp',
        'string': 'text',
        'metadata': 'text', # eew
        }

    def table_exists(self, instance):
        return self._query(instance,
                           '''select relname from pg_class where
                           <dtml-sqltest relname op="eq" type="string">''',
                           {'relname': instance.portal_type.lower()})
