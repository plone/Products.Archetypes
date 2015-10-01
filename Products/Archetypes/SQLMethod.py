from Products.Archetypes.debug import log_exc

from Shared.DC.ZRDB import Aqueduct, RDB
from Shared.DC.ZRDB.Results import Results
from Shared.DC.ZRDB.DA import SQL
from Shared.DC.ZRDB.DA import getBrain
from cStringIO import StringIO
import sys
import types
from ZODB.POSException import ConflictError

from string import atoi
from time import time

try:
    from IOBTree import Bucket
except:
    Bucket = lambda: {}

_defaults = {'max_rows_': 1000,
             'cache_time_': 0,
             'max_cache_': 100,
             'class_name_': '',
             'class_file_': '',
             'template_class': SQL
             }


class SQLMethod(Aqueduct.BaseQuery):

    _arg = None
    _col = None

    def __init__(self, context):
        self.context = context
        self.id = str(context.__class__.__name__)
        self.title = ''
        for k, v in _defaults.items():
            if not hasattr(context, k):
                setattr(context, k, v)

    def edit(self, connection_id, arguments, template):
        """Change database method  properties

        The 'connection_id' argument is the id of a database connection
        that resides in the current folder or in a folder above the
        current folder.  The database should understand SQL.

        The 'arguments' argument is a string containing an arguments
        specification, as would be given in the SQL method cration form.

        The 'template' argument is a string containing the source for the
        SQL Template.
        """
        context = self.context
        self.connection_id = str(connection_id)
        arguments = str(arguments)
        self.arguments_src = arguments
        self._arg = Aqueduct.parse(arguments)
        if not isinstance(template, (str, unicode)):
            template = str(template)
        self.src = template
        self.template = t = context.template_class(template)
        t.cook()
        context._v_query_cache = {}, Bucket()

    def advanced_edit(self, max_rows=1000, max_cache=100, cache_time=0,
                      class_name='', class_file='',
                      REQUEST=None):
        """Change advanced properties

        The arguments are:

        max_rows -- The maximum number of rows to be returned from a query.

        max_cache -- The maximum number of results to cache

        cache_time -- The maximum amound of time to use a cached result.

        class_name -- The name of a class that provides additional
          attributes for result record objects. This class will be a
          base class of the result record class.

        class_file -- The name of the file containing the class
          definition.

        The class file normally resides in the 'Extensions'
        directory, however, the file name may have a prefix of
        'product.', indicating that it should be found in a product
        directory.

        For example, if the class file is: 'ACMEWidgets.foo', then an
        attempt will first be made to use the file
        'lib/python/Products/ACMEWidgets/Extensions/foo.py'. If this
        failes, then the file 'Extensions/ACMEWidgets.foo.py' will be
        used.

        """
        context = self.context
        # paranoid type checking
        if type(max_rows) is not type(1):
            max_rows = atoi(max_rows)
        if type(max_cache) is not type(1):
            max_cache = atoi(max_cache)
        if type(cache_time) is not type(1):
            cache_time = atoi(cache_time)
        class_name = str(class_name)
        class_file = str(class_file)

        context.max_rows_ = max_rows
        context.max_cache_, context.cache_time_ = max_cache, cache_time
        context._v_sql_cache = {}, Bucket()
        context.class_name_, context.class_file_ = class_name, class_file
        context._v_sql_brain = getBrain(context.class_file_,
                                        context.class_name_, 1)

    def _cached_result(self, DB__, query):
        context = self.context
        # Try to fetch from cache
        if hasattr(context, '_v_sql_cache'):
            cache = context._v_sql_cache
        else:
            cache = context._v_sql_cache = {}, Bucket()
        cache, tcache = cache
        max_cache = context.max_cache_
        now = time()
        t = now - context.cache_time_
        if len(cache) > max_cache / 2:
            keys = tcache.keys()
            keys.reverse()
            while keys and (len(keys) > max_cache or keys[-1] < t):
                key = keys[-1]
                q = tcache[key]
                del tcache[key]
                if int(cache[q][0]) == key:
                    del cache[q]
                del keys[-1]

        if query in cache:
            k, r = cache[query]
            if k > t:
                return r

        result = apply(DB__.query, query)
        if context.cache_time_ > 0:
            tcache[int(now)] = query
            cache[query] = now, result

        return result

    def _get_dbc(self):
        """Get the database connection"""
        context = self.context

        try:
            dbc = getattr(context, self.connection_id)
        except AttributeError:
            raise AttributeError, (
                "The database connection <em>%s</em> cannot be found." % (
                    self.connection_id))

        try:
            DB__ = dbc()
        except ConflictError:
            raise
        except:
            raise 'Database Error', (
                '%s is not connected to a database' % self.id)

        return dbc, DB__

    def __call__(self, src__=0, test__=0, **kw):
        """Call the database method

        The arguments to the method should be passed via keyword
        arguments, or in a single mapping object. If no arguments are
        given, and if the method was invoked through the Web, then the
        method will try to acquire and use the Web REQUEST object as
        the argument mapping.

        The returned value is a sequence of record objects.
        """
        context = self.context

        dbc, DB__ = self._get_dbc()

        p = None

        argdata = self._argdata(kw)
        argdata['sql_delimiter'] = '\0'
        argdata['sql_quote__'] = dbc.sql_quote__

        # TODO: Review the argdata dictonary. The line bellow is receiving unicode
        # strings, mixed with standard strings. It is insane! Archetypes needs a policy
        # about unicode, and lots of tests on this way. I prefer to not correct it now,
        # only doing another workarround. We need to correct the cause of this problem,
        # not its side effects :-(

        try:
            query = apply(self.template, (p,), argdata)
        except TypeError, msg:
            msg = str(msg)
            if 'client' in msg:
                raise NameError("'client' may not be used as an " +
                                "argument name in this context")
            else:
                raise

        __traceback_info__ = query

        if src__:
            return query

        # Get the encoding arguments
        # We have two possible kw arguments:
        #   db_encoding:        The encoding used in the external database
        #   site_encoding:      The uncoding used for the site
        # If not specified, we use sys.getdefaultencoding()
        db_encoding = kw.get('db_encoding', None)

        site_encoding = kw.get('site_encoding', 'utf-8')

        if type(query) == type(u''):
            if db_encoding:
                query = query.encode(db_encoding)
            else:
                try:
                    query = query.encode(site_encoding)
                except UnicodeEncodeError:
                    query = query.encode('UTF-8')

        if context.cache_time_ > 0 and context.max_cache_ > 0:
            result = self._cached_result(DB__, (query, context.max_rows_))
        else:
            try:
                result = DB__.query(query, context.max_rows_)
            except ConflictError:
                raise
            except:
                log_exc(msg='Database query failed', reraise=1)

        if hasattr(context, '_v_sql_brain'):
            brain = context._v_sql_brain
        else:
            brain = context._v_sql_brain = getBrain(context.class_file_,
                                                    context.class_name_)

        if type(result) is type(''):
            f = StringIO()
            f.write(result)
            f.seek(0)
            result = RDB.File(f, brain, p, None)
        else:
            if db_encoding:
                # Encode result before we wrap it in Result object
                # We will change the encoding from source to either the specified target_encoding
                # or the site default encoding

                # The data is a list of tuples of column data
                encoded_result = []
                for row in result[1]:
                    columns = ()
                    for col in row:
                        if isinstance(col, types.StringType):
                            # coerce column to unicode with database encoding
                            newcol = unicode(col, db_encoding)
                            # Encode column as string with site_encoding
                            newcol = newcol.encode(site_encoding)
                        else:
                            newcol = col

                        columns += newcol,

                    encoded_result.append(columns)

                result = (result[0], encoded_result)

            result = Results(result, brain, p, None)

        columns = result._searchable_result_columns()

        if test__ and columns != self._col:
            self._col = columns

        # If run in test mode, return both the query and results so
        # that the template doesn't have to be rendered twice!
        if test__:
            return query, result

        return result

    def abort(self):
        dbc, DB__ = self._get_dbc()
        try:
            DB__.tpc_abort()
        except ConflictError:
            raise
        except:
            log_exc(msg='Database abort failed')

    def connectionIsValid(self):
        context = self.context
        return (hasattr(context, self.connection_id) and
                hasattr(getattr(context, self.connection_id), 'connected'))

    def connected(self):
        context = self.context
        return getattr(getattr(context, self.connection_id), 'connected')()
