from Products.Archetypes.SQLMethod import SQLMethod
from Products.Archetypes.interfaces.storage import ISQLStorage
from Products.Archetypes.interfaces.field import IObjectField
from Products.Archetypes.interfaces.layer import ILayer
from Products.Archetypes.config import TOOL_NAME, MYSQL_SQLSTORAGE_TABLE_TYPE
from Products.Archetypes.log import log
from Products.Archetypes.Storage import StorageLayer, type_map
from Acquisition import aq_base, aq_inner, aq_parent
from Products.CMFCore.utils import getToolByName
from ZODB.POSException import ConflictError
from OFS.ObjectManager import BeforeDeleteException
from zope.interface import implements

class BaseSQLStorage(StorageLayer):
    """ SQLStorage Base, more or less ISO SQL """

    implements(ISQLStorage, ILayer)

    query_create = ('create table <dtml-var table> '
                    '(UID char(50) primary key not null, '
                    'PARENTUID char(50), <dtml-var columns>)')
    query_drop   = ('drop table <dtml-var table>')
    query_select = ('select <dtml-var field> from <dtml-var table> '
                    'where <dtml-sqltest UID op="eq" type="string">')
    query_insert = ('insert into <dtml-var table> '
                    'set UID=<dtml-sqlvar UID type="string">, '
                    'PARENTUID=<dtml-sqlvar PARENTUID type="string">')
    query_update = ('update <dtml-var table> set '
                    '<dtml-var field>=<dtml-sqlvar value '
                    'type="%s" optional> where '
                    '<dtml-sqltest UID op="eq" type="string">')
    query_delete = ('delete from <dtml-var table> '
                    'where <dtml-sqltest UID op="eq" type="string">')

    sqlm_type_map = {'integer':'int'}

    db_type_map = {'fixedpoint' : 'integer'}

    def map_object(self, field, value):
        if value is None:
            return 'None'
        else:
            return value

    def unmap_object(self, field, value):
        if value == 'None':
            return None
        else:
            return value

    def map_datetime(self, field, value):
        # we don't want to lose even 0.001 second
        try:
            return value.ISO()[:-2] + str(value.second())
        except:
            return None

    def map_fixedpoint(self, field, value):
        __traceback_info__ = repr(value)
        template = '%%d%%0%dd' % field.precision
        return template % value

    def unmap_fixedpoint(self, field, value):
        __traceback_info__ = repr(value)
        if value is None or value == '':
            return (0, 0)
        if type(value) == type(''):   # Gadfly return integers as strings
            value = int(value)
        split = 10 ** field.precision
        return (value / split), (value % split)

    def map_lines(self, field, value):
        __traceback_info__ = repr(value)
        return '\n'.join(value)

    def unmap_lines(self, field, value):
        __traceback_info__ = repr(value)
        return value.split('\n')

    def map_boolean(self, field, value):
        __traceback_info__ = repr(value)
        if not value:
            return 0
        else:
            return 1

    def map_reference(self, field, value):
        __traceback_info__ = repr(value)

        return ','.join(value)

    def unmap_boolean(self, field, value):
        __traceback_info__ = repr(value)
        if not value or value == '0':   # Gadfly return integers as strings
            return 0
        else:
            return 1

    def table_exists(self, instance):
        raise NotImplemented

    def is_initialized(self, instance):
        try:
            return self.getName() in instance.__initialized
        except AttributeError:
            return None

    def initializeField(self, instance, field):
        pass

    def is_cleaned(self, instance):
        try:
            return self.getName() in instance.__cleaned
        except AttributeError:
            return None

    def cleanupField(self, instance, field):
        pass

    def _query(self, instance, query, args):
        c_tool = getToolByName(instance, TOOL_NAME)
        connection_id = c_tool.getConnFor(instance)
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), query)
        query, result = method(test__=1, **args)
        return result

    def initializeInstance(self, instance, item=None, container=None):
        if (self.is_initialized(instance) or
            getattr(instance, '_at_is_fake_instance', None)):
            # duh, we don't need to be initialized twice
            return
        factory = getToolByName(instance,'portal_factory')
        if factory.isTemporary(instance):
          return

        fields = instance.Schema().fields()
        fields = [f for f in fields if IObjectField.providedBy(f) \
                  and f.getStorage().__class__ is self.__class__]
        columns = []
        args = {}
        for field in fields:
            type = self.db_type_map.get(field.type, field.type)
            name = field.getName()
            # MySQL supports escape for columns names!
            if self.__class__.__name__ == 'MySQLSQLStorage':
                columns.append('`%s` %s' % (name, type))
            else:
                columns.append('%s %s' % (name, type))
        parent = container or aq_parent(aq_inner(instance))
        args['PARENTUID'] = getattr(aq_base(parent), 'UID', lambda: None)()
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        #args['db_encoding']=kwargs.get('db_encoding',None)
        args['columns'] = ', ' + ', '.join(columns)
        if not self.table_exists(instance):
            self._query(instance, self.query_create, args)
            log('created table %s\n' % args['table'])
        try:
            self._query(instance, self.query_insert, args)
        except ConflictError:
            raise
        except:
            # usually, duplicate key
            # raise SQLInitException(msg)
            raise
        try:
            instance.__initialized += (self.getName(),)
        except AttributeError:
            instance.__initialized = (self.getName(),)
        # now, if we find an attribute called _v_$classname_temps, it
        # means the object was moved and we can initialize the fields
        # with those values
        temps_var = '_v_%s_temps' % self.getName()
        if hasattr(aq_base(instance), temps_var):
            temps = getattr(instance, temps_var)
            for key, value in temps.items():
                instance.Schema()[key].set(instance, value)
            delattr(instance, temps_var)
        try:
            del instance.__cleaned
        except (AttributeError, KeyError):
            pass

    def get(self, name, instance, **kwargs):
        if not self.is_initialized(instance):
            # ignore all calls before we're initialized - some
            # manage_afterAdd() methods try to get and set fields and
            # we can't allow that to break
            return None
        field = kwargs.get('field', instance.getField(name))
        args = {}
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        args['db_encoding']=kwargs.get('db_encoding',None)
        args['field'] = name
        result = self._query(instance, self.query_select, args)
        result = result[0][0]
        mapper = getattr(self, 'unmap_' + field.type, None)
        if mapper is not None:
            result = mapper(field, result)
        return result

    def set(self, name, instance, value, **kwargs):
        if not self.is_initialized(instance):
            # ignore all calls before we're initialized - some
            # manage_afterAdd() methods try to get and set fields and
            # we can't allow that to break
            return None
        field = kwargs.get('field', instance.getField(name))
        mapper = getattr(self, 'map_' + field.type, None)
        if mapper is not None:
            value = mapper(field, value)
        type = type_map.get(field.type, 'string')
        sql_type = self.sqlm_type_map.get(field.type, 'string')
        default = field.default
        args = {}
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        #args['db_encoding']=kwargs.get('db_encoding',None)
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

    def cleanupInstance(self, instance, item=None, container=None):
        if (self.is_cleaned(instance) or
            getattr(instance, '_at_is_fake_instance', None)):
            # duh, we don't need to be cleaned twice
            return
        # the object is being deleted. remove data from sql.  but
        # first, made a temporary copy of the field values in case we
        # are being moved
        fields = instance.Schema().fields()
        fields = [f for f in fields if IObjectField.providedBy(f) \
                  and f.getStorage().__class__ is self.__class__]
        temps = {}
        for f in fields:
            temps[f.getName()] = f.get(instance)
        setattr(instance, '_v_%s_temps' % self.getName(), temps)
        # now, remove data from sql
        c_tool = getToolByName(instance, TOOL_NAME)
        connection_id = c_tool.getConnFor(instance)
        args = {}
        args['table'] = instance.portal_type
        args['UID'] = instance.UID()
        #args['db_encoding']=kwargs.get('db_encoding',None)
        method = SQLMethod(instance)
        method.edit(connection_id, ' '.join(args.keys()), self.query_delete)
        try:
            query, result = method(test__=1, **args)
        except ConflictError:
            raise
        except:
            # dunno what could happen here raise
            # SQLCleanupException(msg)
            raise BeforeDeleteException
        try:
            instance.__cleaned += (self.getName(),)
        except AttributeError:
            instance.__cleaned = (self.getName(),)
        try:
            del instance.__initialized
        except (AttributeError, KeyError):
            pass

class GadflySQLStorage(BaseSQLStorage):

    query_create = ('create table <dtml-var table> '
                    '(UID varchar, PARENTUID varchar <dtml-var columns>)')
    query_select = ('select <dtml-var field> from <dtml-var table> '
                    'where <dtml-sqltest UID op="eq" type="string">')
    query_insert = ('insert into <dtml-var table> '
                    'values (<dtml-sqlvar UID type="string">, '
                    '<dtml-sqlvar PARENTUID type="string">, '
                    '<dtml-in expr="_.string.split(columns,\',\')[1:]"> '
                    '<dtml-if sequence-end>\'\'<dtml-else>\'\', </dtml-if> '
                    '</dtml-in>) ')
    query_update = ('update <dtml-var table> set '
                    '<dtml-var field>=<dtml-sqlvar value '
                    'type="%s" optional> where '
                    '<dtml-sqltest UID op="eq" type="string">')
    query_delete = ('delete from <dtml-var table> '
                    'where <dtml-sqltest UID op="eq" type="string">')

    sqlm_type_map = {'integer':'string',
                     'float':'string'}

    db_type_map = {'object'     : 'varchar',
                   'string'     : 'varchar',
                   'text'       : 'varchar',
                   'datetime'   : 'varchar',
                   'integer'    : 'varchar',
                   'float'      : 'varchar',
                   'fixedpoint' : 'integer',
                   'lines'      : 'varchar',
                   'reference'  : 'varchar',
                   'boolean'    : 'integer',
                   }

    def map_datetime(self, field, value):
        try:
            return value.ISO()[:-2] + str(value.second())
        except:
            return ''

    def unmap_datetime(self, field, value):
        from DateTime import DateTime
        try:
            return DateTime(value)
        except:
            return None

    def map_integer(self, field, value):
        __traceback_info__ = repr(value)
        if value is None:   # Gadfly represents None as an empty string
            return ''
        else:
            return str(value)

    def unmap_integer(self, field, value):
        __traceback_info__ = repr(value)
        if value == '':   # Gadfly represents None as an empty string
            return None
        else:
            return int(value)

    def map_float(self, field, value):
        __traceback_info__ = repr(value)
        if value is None:   # Gadfly represents None as an empty string
            return ''
        else:
            return str(value)

    def unmap_float(self, field, value):
        __traceback_info__ = repr(value)
        if value == '':   # Gadfly represents None as an empty string
            return None
        else:
            return float(value)

    def unmap_lines(self, field, value):
        __traceback_info__ = repr(value)
        if value == '':   # Gadfly represents None as an empty String
            return None
        else:
            return value.split('\n')

    def table_exists(self, instance):
        try:
            self._query(instance,
                        'select * from <dtml-var table>',
                        {'table': instance.portal_type.lower()})
        except ConflictError:
            raise
        except:
            return 0
        else:
            return 1

class MySQLSQLStorage(BaseSQLStorage):

    query_create = ('create table `<dtml-var table>` '
                    '(UID char(50) primary key not null, '
                    'PARENTUID char(50) <dtml-var columns>) TYPE = %s' % MYSQL_SQLSTORAGE_TABLE_TYPE)
    query_select = ('select `<dtml-var field>` '
                    'from `<dtml-var table>` where '
                    '<dtml-sqltest UID op="eq" type="string">')
    query_insert = ('insert into `<dtml-var table>` '
                    'set UID=<dtml-sqlvar UID type="string">, '
                    'PARENTUID=<dtml-sqlvar PARENTUID type="string">')
    query_update = ('update `<dtml-var table>` set '
                    '`<dtml-var field>`=<dtml-sqlvar value '
                    'type="%s" optional> where '
                    '<dtml-sqltest UID op="eq" type="string">')
    query_delete = ('delete from `<dtml-var table>` '
                    'where <dtml-sqltest UID op="eq" type="string">')

    db_type_map = {'object'     : 'text',
                   'string'     : 'text',
                   'fixedpoint' : 'integer',
                   'lines'      : 'text',
                   'reference'  : 'text',
                   'boolean'    : 'tinyint',
                   }

    def table_exists(self, instance):
        result =  [r[0].lower() for r in
                   self._query(instance, '''show tables''', {})]
        return instance.portal_type.lower() in result

class PostgreSQLStorage(BaseSQLStorage):

    query_create = ('create table <dtml-var table> '
                    '(UID text primary key not null, '
                    'PARENTUID text <dtml-var columns>)')
    query_select = ('select <dtml-var field> from <dtml-var table> '
                    'where <dtml-sqltest UID op="eq" type="string">')
    query_insert = ('insert into <dtml-var table> '
                    '(UID, PARENTUID) values '
                    '(<dtml-sqlvar UID type="string">, '
                    '<dtml-sqlvar PARENTUID type="string">)')
    query_update = ('update <dtml-var table> set '
                    '<dtml-var field>=<dtml-sqlvar value '
                    'type="%s" optional> where '
                    '<dtml-sqltest UID op="eq" type="string">')
    query_delete = ('delete from <dtml-var table> '
                    'where <dtml-sqltest UID op="eq" type="string">')

    db_type_map = {'object'     : 'text',
                   'string'     : 'text',
                   'datetime'   : 'timestamp',
                   'fixedpoint' : 'integer',
                   'lines'      : 'text',
                   'reference'  : 'text',
                   }

    def table_exists(self, instance):
        return self._query(instance,
                           ('select relname from pg_class where '
                            '<dtml-sqltest relname op="eq" type="string">'),
                           {'relname': instance.portal_type.lower()})

class SQLServerStorage(BaseSQLStorage):

    query_create = ('create table <dtml-var table> '
                    '(UID varchar(50) CONSTRAINT pk_uid '
                    'PRIMARY KEY CLUSTERED, '
                    'PARENTUID varchar(50) '
                    '<dtml-var columns>)')
    query_select = ('select <dtml-var field> from '
                    '<dtml-var table> '
                    'where <dtml-sqltest UID op="eq" type="string">')
    query_insert = ('insert into <dtml-var table> '
                    '(UID, PARENTUID) values '
                    '(<dtml-sqlvar UID type="string">, '
                    '<dtml-sqlvar PARENTUID type="string">)')
    query_update = ('update <dtml-var table> set '
                    '<dtml-var field>=<dtml-sqlvar value '
                    'type="%s" optional> where '
                    '<dtml-sqltest UID op="eq" type="string">')
    query_delete = ('delete from <dtml-var table> '
                    'where <dtml-sqltest UID op="eq" type="string">')

    db_type_map = {'object'     : 'varchar',
                   'string'     : 'varchar',
                   'text'       : 'varchar',
                   'datetime'   : 'timestamp',
                   'fixedpoint' : 'integer',
                   'lines'      : 'varchar',
                   'reference'  : 'varchar',
                   'boolean'    : 'integer',
                   }

    def table_exists(self, instance):
        return self._query(instance,
                           ('select name from '
                            'sysobjects where '
                            'xtype=char(85) and uid=1 and '
                            '<dtml-sqltest name op="eq" type="string">'),
                           {'name':instance.portal_type.lower()})
