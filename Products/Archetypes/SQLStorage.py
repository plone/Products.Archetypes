from Products.CMFCore.utils import getToolByName
from SQLMethod import SQLMethod
from interfaces.storage import IStorage, ISQLStorage
from interfaces.field import IObjectField
from interfaces.layer import ILayer
from exceptions import SQLInitException
from debug import log
from config import TOOL_NAME
from Storage import *

class BaseSQLStorage(StorageLayer):
    # SQLStorage that is more or less ISO SQL, should be usable as a base
    __implements__ = (ISQLStorage, ILayer)

    column_template = "%(name)s not null default %(default)s"
    query_create = """create table <dtml-var table> \
                      (UID char(50) primary key not null <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> \
                      set UID=<dtml-sqlvar UID type="string">"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s"> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""

    sqlm_type_map = {'integer':'int'}
    db_type_map = {}
    
    def initalizeInstance(self, instance):
        c_tool = getToolByName(instance, TOOL_NAME)
        connection_id = c_tool.getConnFor(instance)
        fields = instance.Schema().fields()
        fields = [f for f in fields if IObjectField.isImplementedBy(f) \
                  and ISQLStorage.isImplementedBy(f.getStorage())]
        columns = []
        args = {}
        for field in fields:
            type = self.db_type_map.get(field.type, field.type)
            name = field.name
            default = field.default
            column = '%s %s' % (name, type)
            if default is not None:
                if type == 'text':
                    default = "'%s'" % default
                column = self.column_template % {'name': column, 'default': default}
            columns.append(column)
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        args['columns'] = ', ' + ', '.join(columns)
        # print args['columns']
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), self.query_create)
        try:
            query, result = method(test__=1, **args)
            # print query
        except Exception, msg:
            # usually, table already exists
            # raise SQLInitException(msg)
            if not str(msg).endswith('exists'):
                raise

        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), self.query_insert)
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
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), self.query_select)
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
        sql_type = self.sqlm_type_map.get(field.type, 'string')
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
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), self.query_update % sql_type)
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
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), self.query_delete)
        try:
            query, result = method(test__=1, **args)
        except Exception, msg:
            # dunno what could happen here
            # raise SQLCleanupException(msg)
            pass

    def initalizeField(self, instance, field):
        pass

    def cleanupField(self, instance, field):
        pass
    

class GadflySQLStorage(BaseSQLStorage):
    __implements__ = BaseSQLStorage.__implements__

    column_template = "%(name)s"
    query_create = """create table <dtml-var table> \
                      (UID varchar <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> \
                      set UID=<dtml-sqlvar UID type="string">"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s"> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""

    sqlm_type_map = {'integer':'int'}
    db_type_map = {'text': 'varchar',
                   'object': 'varchar',}


class MySQLStorage(BaseSQLStorage):
    __implements__ = BaseSQLStorage.__implements__

    query_create = """create table <dtml-var table> \
                      (UID char(50) primary key not null <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> \
                      set UID=<dtml-sqlvar UID type="string">"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s"> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""

    sqlm_type_map = {'integer':'int'}
    db_type_map = {}


class OracleSQLStorage(BaseSQLStorage):
    __implements__ = BaseSQLStorage.__implements__

    query_create = """create table <dtml-var table> \
                      (UID char(50) primary key not null <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> \
                      set UID=<dtml-sqlvar UID type="string">"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s"> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""

    sqlm_type_map = {'integer':'int'}
    db_type_map = {}
    

class PostgreSQLStorage(BaseSQLStorage):
    __implements__ = BaseSQLStorage.__implements__

    query_create = """create table <dtml-var table> \
                      (UID char(50) primary key not null <dtml-var columns>)"""
    query_insert = """insert into <dtml-var table> \
                      set UID=<dtml-sqlvar UID type="string">"""
    query_select = """select <dtml-var field> from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""
    query_update = """update <dtml-var table> set <dtml-var field>=<dtml-sqlvar value type="%s"> \
                      where  <dtml-sqltest UID op="eq" type="string">"""
    query_delete = """delete from <dtml-var table> \
                      where <dtml-sqltest UID op="eq" type="string">"""

    sqlm_type_map = {'integer':'int'}
    db_type_map = {}
