from Acquisition import aq_base
from AccessControl import getSecurityManager
from Products.CMFCore.utils import getToolByName
from Products.CMFCore.CMFCatalogAware import CMFCatalogAware
from Products.CMFCore import CMFCorePermissions

from ExtensionClass import Base
import OFS.Moniker
from OFS.CopySupport import _cb_decode, cookie_path, \
     CopyContainer, CopySource, eNoData, eInvalid, \
     eNotFound, eNotSupported

import config
from debug import log, log_exc

####
## In the case of a copy we want to lose refs
##                a cut/paste we want to keep refs
##                a delete to lose refs
####

class Referenceable(CMFCatalogAware, Base):
    isReferenceable = 1

    def getRefs(self):
        """get all the referenced objects for this object"""
        tool = getToolByName(self, config.TOOL_NAME)
        return [tool.getObject(ref) for ref in tool.getRefs(self)]

    def getBRefs(self):
        """get all the back referenced objects for this object"""
        tool = getToolByName(self, config.TOOL_NAME)
        return [tool.getObject(ref) for ref in tool.getBRefs(self)]
    

    
    def _register(self, archetype_tool=None):
        """register with the archetype tool for a unique id"""
        if hasattr(aq_base(self), '_uid') and self._uid is not None:
            return
        
        try:
            if not archetype_tool:
                archetype_tool = getToolByName(self, config.TOOL_NAME)
            cid = archetype_tool.registerContent(self)
            #log("Registered Content Object with cid: %s from ID %s" % (cid, self.getId()))
        except:
            log_exc()

    def _unregister(self):
        """unregister with the archetype tool, remove all references"""
        try:
            archetype_tool = getToolByName(self, config.TOOL_NAME)
            cid = archetype_tool.unregisterContent(self)
            #log("unreg", cid)
        except:
            log_exc()
        
    def UID(self):
        #self._register() #Comment out soon
        return self._getUID()
    
    def _getUID(self):
        return getattr(aq_base(self), '_uid', None)

    def _setUID(self, id):
        tid =  self._getUID()
        if not tid:
            self._uid = id

    ## Hooks
    def manage_afterAdd(self, item, container):
        """
        Get a UID
        (Called when the object is created or moved.)
        """
        ct = getToolByName(container, config.TOOL_NAME, None)
        if ct:
            self._register(archetype_tool=ct)
        Referenceable.inheritedAttribute('manage_afterAdd')(self, item, \
                                                            container)
        
    def manage_afterClone(self, item):
        """
        Get a new UID
        (Called when the object is cloned.)
        """
        self._uid = None
        self._register()
        Referenceable.inheritedAttribute('manage_afterClone')(self, item)
        
    def manage_beforeDelete(self, item, container):
        """
            Remove self from the catalog.
            (Called when the object is deleted or moved.)
        """
        #log("deleting %s:%s" % (self.getId(), self.UID()))
        #log("self, item, container", self, item, container)
        
        storeRefs = getattr(self, '_cp_refs', None)

        if not storeRefs: self._unregister()

        #and reset the flag
        self._cp_refs = None
        Referenceable.inheritedAttribute('manage_beforeDelete')(self, item, \
                                                            container)

    def pasteReference(self, REQUEST=None):
        """
        Use the copy support buffer to paste object references into this object.
        I think I am being tricky.
        """
        cp=None
        if REQUEST and REQUEST.has_key('__cp'):
            cp=REQUEST['__cp']
        if cp is None:
            raise "No cp data"
        
        try:
            cp=_cb_decode(cp)
        except:
            raise "can't decode cp: %r" % cp

        oblist=[]
        app = self.getPhysicalRoot()

        for mdata in cp[1]:
            m = OFS.Moniker.loadMoniker(mdata)
            try: ob = m.bind(app)
            except: raise "Objects not found in %s" % app
            self._verifyPasteRef(ob) ##TODO fix this
            oblist.append(ob)

        ct = getToolByName(self, config.TOOL_NAME)
        
        for ob in oblist:
            if getattr(ob, 'isReferenceable', None):
                ct.addReference(self, ob)
                
                
        if REQUEST is not None:
            REQUEST['RESPONSE'].setCookie('__cp', 'deleted',
                                          path='%s' % cookie_path(REQUEST),
                                          expires='Wed, 31-Dec-97 23:59:59 GMT')
            REQUEST['__cp'] = None
            return REQUEST.RESPONSE.redirect(self.absolute_url() + "/reference_edit")
        return ''

    
    def _notifyOfCopyTo(self, container, op=0):
        """keep reference info internally when op == 1 (move)
        because in those cases we need to keep refs"""
        ## This isn't really safe for concurrent usage, but the
        ## worse case is not that bad and could be fixed with a reindex
        ## on the archetype tool
        if op==1: self._cp_refs =  1 

        
    def _verifyPasteRef(self, object):
        # Verify whether the current user is allowed to paste the
        # passed object into self. This is determined by checking
        # to see if the user could create a new object of the same
        # meta_type of the object passed in and checking that the
        # user actually is allowed to access the passed in object
        # in its existing context.
        #
        # Passing a false value for the validate_src argument will skip
        # checking the passed in object in its existing context. This is
        # mainly useful for situations where the passed in object has no 
        # existing context, such as checking an object during an import
        # (the object will not yet have been connected to the acquisition
        # heirarchy).
        if not hasattr(object, 'meta_type'):
            raise 'The object <EM>%s</EM> does not support this ' \
                  'operation' % absattr(object.id)
        mt=object.meta_type
        if not hasattr(self, 'all_meta_types'):
            raise 'Cannot paste into this object.'

        mt_permission=CMFCorePermissions.ModifyPortalContent
        if getSecurityManager().checkPermission( mt_permission, self ):
            # Ensure the user is allowed to access the object on the
            # clipboard.
            try:    parent=aq_parent(aq_inner(object))
            except: parent=None
            if getSecurityManager().validate(None, parent, None, object):
                return
            raise Unauthorized, absattr(object.id)
        else:
            raise Unauthorized(permission=mt_permission)


    def _verifyObjectPaste(self, object, validate_src=1):
        self._verifyPasteRef(object)
        
