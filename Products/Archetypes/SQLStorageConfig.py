""" SQL Storage Configuration for Archetypes.
"""
from Products.Archetypes.config import TOOL_NAME
from Products.Archetypes.interfaces.storage import ISQLStorage
from Products.Archetypes.interfaces.field import IObjectField

from AccessControl import ClassSecurityInfo
from Acquisition import aq_base
from App.class_init import InitializeClass
from App.special_dtml import DTMLFile
from OFS.SimpleItem import SimpleItem
from Persistence import PersistentMapping
from Products.CMFCore.permissions import ManagePortal
from Products.CMFCore.utils import getToolByName

class SQLStorageConfig (SimpleItem):

    """ Map Archetypes to SQL Database Connections.
    """

    meta_type = 'SQL Storage Config'

    _conn_by_type = None  # PersistentMapping
    _default_conn = None

    security = ClassSecurityInfo()

    manage_options = (({ 'label' : 'Connections'
                         , 'action' : 'manage_selectConnections'
                         }
                       ),
                      )

    #
    #   ZMI methods
    #


    _manage_selectConnections = DTMLFile('www/selectConnections', globals())

    security.declareProtected( ManagePortal, 'manage_selectConnections')
    def manage_selectConnections(self, REQUEST, manage_tabs_message=None):

        """ Show a management screen for changing type to workflow connections.
        """
        cbt = self._conn_by_type
        ti = self.getConfigurableTypes()
        types_info = []
        for t in ti:
            id = t['name']
            title = None
            if cbt is not None and cbt.has_key(id):
                conn = cbt[id]
            else:
                conn = '(Default)'
            types_info.append({'id': id,
                               'title': title,
                               'conn': conn})
        return self._manage_selectConnections(
            REQUEST,
            default_conn=self._default_conn,
            types_info=types_info,
            management_view='Connections',
            manage_tabs_message=manage_tabs_message)

    security.declareProtected( ManagePortal, 'manage_changeConnections')
    def manage_changeConnections(self, default_conn, props=None, REQUEST=None):
        """ Changes which connectionss apply to objects of which type.
        """
        if props is None:
            props = REQUEST
        cbt = self._conn_by_type
        if cbt is None:
            self._conn_by_type = cbt = PersistentMapping()
        ti = self.getConfigurableTypes()
        types_info = []
        for t in ti:
            id = t['name']
            field_name = 'conn_%s' % id
            conn = props.get(field_name, '(Default)').strip()
            self.setConnForPortalTypes((id, ), conn)

        # Set up the default conn.
        self.setDefaultConn(default_conn)
        if REQUEST is not None:
            return self.manage_selectConnections(REQUEST,
                            manage_tabs_message='Changed.')

    #
    #   Administration methods
    #
    security.declareProtected( ManagePortal, 'setDefaultConn')
    def setDefaultConn(self, default_conn):
        """ Set the default conn for this tool
        """
        default_conn = default_conn.strip()
        if default_conn:
            if not self.getConnectionById(default_conn):
                raise ValueError, (
                    '"%s" is not a valid SQL Connector.' % default_conn)
        self._default_conn = default_conn

    security.declarePrivate('getDefaultConnFor')
    def getDefaultConnFor(self, ob):
        """ Return the default conn, if applicable, for ob.
        """

        types_tool = getToolByName( self, 'portal_types', None )
        if ( types_tool is not None
            and types_tool.getTypeInfo( ob ) is not None ):
            return self._default_conn
        return None

    security.declareProtected( ManagePortal, 'getConfigurableTypes')
    def getConfigurableTypes(self):
        """ Get a list of types that can be configured for SQL Storage.
        """
        c_types = []
        ti = self.getInstalledTypes()
        for t in ti:
            for field in t['schema'].fields():
                if IObjectField.providedBy(field) and \
                   ISQLStorage.providedBy(field.getStorage()):
                    c_types.append(t)
                    break
        return c_types


    security.declareProtected( ManagePortal, 'getInstalledTypes')
    def getInstalledTypes(self):
        pt = getToolByName(self, 'portal_types', None)
        at = getToolByName(self, TOOL_NAME, None)
        if pt is None:
            return ()
        if at is None:
            return ()
        pt = pt.listTypeInfo()
        pt = [t.getId() for t in pt]

        ti = at.listRegisteredTypes()

        installed_types = [t for t in ti if t['name'] in pt]
        return installed_types


    security.declareProtected( ManagePortal, 'setConnForPortalTypes')
    def setConnForPortalTypes(self, type_names, conn):
        """ Set a conn for a specific portal type.
        """
        cbt = self._conn_by_type

        if cbt is None:
            self._conn_by_type = cbt = PersistentMapping()

        for id in type_names:
            if conn == '(Default)':
                # Remove from cbt.
                if cbt.has_key(id):
                    del cbt[id]
            else:
                conn = conn.strip()
                if conn:
                    if not self.getConnectionById(conn):
                        raise ValueError, (
                            '"%s" is not a valid SQL Connector.' % conn)
                cbt[id] = conn

    security.declarePrivate('getConnectionById')
    def getConnectionById(self, conn_id):
        """ Retrieve a given Connection.
        """
        conn = getattr(self, conn_id, None)
        return conn

    security.declarePrivate('getConnFor')
    def getConnFor(self, ob):
        """ Returns the conn that applies to the given object.
            If we get a string as the ob parameter, use it as
            the portal_type.
        """
        cbt = self._conn_by_type
        if type(ob) == type(''):
            pt = ob
        elif hasattr(aq_base(ob), '_getPortalTypeName'):
            pt = ob._getPortalTypeName()
        else:
            pt = None

        if pt is None:
            return None

        conn = None
        if cbt is not None:
            conn = cbt.get(pt, None)
            # Note that if conn is not in cbt or has a value of
            # None, we use a default conn.
        if conn is None:
            conn = self.getDefaultConnFor(ob)
            if conn is None:
                return ''
        return conn

InitializeClass(SQLStorageConfig)
