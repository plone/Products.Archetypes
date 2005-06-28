From kai.hoppert@tomcom.de Mon Jun 20 10:44:12 2005
Return-path: <kai.hoppert@tomcom.de>
Envelope-to: jens.klein@jensquadrat.de
Delivery-date: Mon, 20 Jun 2005 10:44:12 +0200
Received: from localhost ([127.0.0.1]) by server1.fischkopf.org with esmtp
	(Exim 4.30) id 1DkHt6-0001XL-3p for jens.klein@jensquadrat.de; Mon, 20 Jun
	2005 10:44:12 +0200
Received: from server1.fischkopf.org ([127.0.0.1]) by localhost (server1
	[127.0.0.1]) (amavisd-new, port 10024) with ESMTP id 05649-09 for
	<jens.klein@jensquadrat.de>; Mon, 20 Jun 2005 10:44:06 +0200 (CEST)
Received: from tom-com.de ([217.160.129.118] helo=tc1.tcis.de) by
	server1.fischkopf.org with esmtp (Exim 4.30) id 1DkHt0-0001X5-4J for
	jens.klein@jensquadrat.de; Mon, 20 Jun 2005 10:44:06 +0200
Received: from pd9501689.dip0.t-ipconnect.de ([217.80.22.137] helo=zopelab)
	by tc1.tcis.de with asmtp (Exim 3.35 #1) id 1DkHwG-0007TX-00 for
	jens.klein@jensquadrat.de; Mon, 20 Jun 2005 10:47:28 +0200
From: "Kai Hoppert" <kai.hoppert@tomcom.de>
To: <jens.klein@jensquadrat.de>
Subject: Neues get_site
Date: Mon, 20 Jun 2005 10:45:40 +0200
Message-ID: <6BB4B8BDA20DE24BA6177A11A56EEDD506C2AA@outlook.tomcom.de>
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="----=_NextPart_000_00B7_01C57585.D4158F10"
X-Priority: 3 (Normal)
X-MSMail-Priority: Normal
X-Mailer: Microsoft Outlook CWS, Build 9.0.6604 (9.0.2911.0)
X-MimeOLE: Produced By Microsoft MimeOLE V6.00.2800.1441
Importance: Normal
X-Virus-Scanned: by amavisd-new-20030616-p10 at fischkopf.org
Status: RO
X-UID: 18233
Content-Length: 15099
X-Keywords:                                                                
	                                  
X-Evolution-Source: imap://jensens@jensquadrat.com/


------=_NextPart_000_00B7_01C57585.D4158F10
Content-Type: text/plain; charset="iso-8859-1"
Content-Transfer-Encoding: 8bit

Hi,

hier mal ein diff und das der size storage.

gedifft hab ich gegen 1.3.3-branch. Die size.py liegt in Archetypes/Storage.

Leider hab ich es noch nicht geschafft nen unitest dazu zu schreiben :( ich
hoffe ich komm die Woche noch dazu. Vielleicht findet ja auch jemand anderes
Zeit dazu.... Christian meint du sollst es erst mal als Branch einchecken.

Bei der Frage "Welche Felder im einzelnen für die größe eines Objektes
zusammengerechnet werden solle" gibt es sicherlich noch Optimierungsbedarf.
ist aber alles über size_significant an jedem feld einstellbar.

Ausgenommen hab ich erst mal alles Zahlen und Boolean Felder.

Wenn noch was sein sollte ich bin im IRC oder per mail erreichbar.

Mit freundlichen Grüßen vom Bodensee,

Kai Hoppert
___________________________________________________
tomcom Gesellschaft für Informationstechnologie mbH
Peter-Dornier-Str. 2 | D-88131 Lindau
Fon +49 (0)8382 275833-0 | Fax +49 (0)8382 275833-33
kai.hoppert@tomcom.de | http://www.tomcom.de

This document should only be read by those persons to whom it is addressed
and is not intended to be relied upon by any person without subsequent
written confirmation of its contents.  tomcom disclaims all responsibility
and accepts no liability for the consequences of any person acting, or
refraining from acting on the contents of this document.  Any unauthorised
form of dissemination, copying, disclosure, modification, distribution
and/or publication of this message is strictly prohibited. For information
about tomcom please contact us on +49.8382.975844 or visit our web site at
www.tomcom.de



------=_NextPart_000_00B7_01C57585.D4158F10
Content-Type: text/plain; name="diff.txt"
Content-Disposition: attachment; filename="diff.txt"
Content-Transfer-Encoding: 8bit

Index: interfaces/storage.py
===================================================================
--- interfaces/storage.py	(revision 4469)
+++ interfaces/storage.py	(working copy)
@@ -22,3 +22,9 @@
 class ISQLStorage(IStorage):
     """ Marker interface for distinguishing ISQLStorages """
     pass
+
+class ISizeableStorage(Interface):
+    """This Interface is for noticing if
+       he is competent to calculates the size of stored data.
+    """
+    pass
Index: BaseObject.py
===================================================================
--- BaseObject.py	(revision 4469)
+++ BaseObject.py	(working copy)
@@ -580,7 +580,10 @@
         """ Used for FTP and apparently the ZMI now too """
         size = 0
         for field in self.Schema().fields():
-            size+=field.get_size(self)
+            if getattr(field,'size_significant',False):
+                print field
+                print field.get_size(self)
+                size+=field.get_size(self)
         return size
 
     security.declarePrivate('_processForm')
Index: Field.py
===================================================================
--- Field.py	(revision 4469)
+++ Field.py	(working copy)
@@ -34,7 +34,7 @@
 
 from Products.Archetypes.config import REFERENCE_CATALOG
 from Products.Archetypes.Layer import DefaultLayerContainer
-from Products.Archetypes.interfaces.storage import IStorage
+from Products.Archetypes.interfaces.storage import IStorage,ISizeableStorage
 from Products.Archetypes.interfaces.base import IBaseUnit
 from Products.Archetypes.interfaces.field import IField
 from Products.Archetypes.interfaces.field import IObjectField
@@ -237,6 +237,7 @@
                                          # are the accessor and edit accessor
         'schemata' : 'default',
         'languageIndependent' : False,
+        'size_significant' : False,
         }
 
     def __init__(self, name=None, **kwargs):
@@ -666,6 +667,16 @@
         """ Checks if the user may edit this field and if
         external editor is enabled on this instance """
 
+    security.declarePublic('get_size')
+    def get_size(self, instance):
+        """Only returnes the cached size from annotations storage
+        """
+        size=0
+        storage=self.getStorage(instance)
+        if ISizeableStorage.isImplementedBy(storage):
+            size=storage.get_size(self.getName(), instance)
+        return size  
+
 #InitializeClass(Field)
 setSecurity(Field)
 
@@ -682,6 +693,7 @@
     _properties.update({
         'type' : 'object',
         'default_content_type' : 'application/octet',
+        'size_significant' : True,
         })
 
     security  = ClassSecurityInfo()
@@ -791,21 +803,6 @@
                                'application/octet-stream')
         return mimetype
 
-    security.declarePublic('get_size')
-    def get_size(self, instance):
-        """Get size of the stored data used for get_size in BaseObject
-
-        Should be overwritte by special fields like FileField. It's safe for
-        fields which are storing strings, ints and BaseUnits but it won't return
-        the right results for fields containing OFS.Image.File instances or
-        lists/tuples/dicts.
-        """
-        data = self.getRaw(instance)
-        try:
-            return len(data)
-        except (TypeError, AttributeError):
-            return len(str(data))
-
 #InitializeClass(ObjectField)
 setSecurity(ObjectField)
 
@@ -816,6 +813,7 @@
         'type' : 'string',
         'default': '',
         'default_content_type' : 'text/plain',
+        'size_significant' : True,
         })
 
     security  = ClassSecurityInfo()
@@ -847,6 +845,7 @@
         'widget' : FileWidget,
         'content_class' : File,
         'default_content_type' : 'application/octet',
+        'size_significant' : True,
         })
 
     security  = ClassSecurityInfo()
@@ -1122,16 +1121,6 @@
             RESPONSE = REQUEST.RESPONSE
         return file.index_html(REQUEST, RESPONSE)
 
-    security.declarePublic('get_size')
-    def get_size(self, instance):
-        """Get size of the stored data used for get_size in BaseObject
-        """
-        file = self.get(instance)
-        if isinstance(file, self.content_class):
-            return file.get_size()
-        # Backwards compatibility
-        return len(str(file))
-
 class TextField(FileField):
     """Base Class for Field objects that rely on some type of
     transformation"""
@@ -1148,6 +1137,7 @@
         'allowable_content_types' : ('text/plain',),
         'primary' : False,
         'content_class': BaseUnit,
+        'size_significant' : True,
         })
 
     security  = ClassSecurityInfo()
@@ -1308,12 +1298,6 @@
         """
         return self.get(instance, raw=True)
 
-    security.declarePublic('get_size')
-    def get_size(self, instance):
-        """Get size of the stored data used for get_size in BaseObject
-        """
-        return len(self.getBaseUnit(instance))
-
 class DateTimeField(ObjectField):
     """A field that stores dates and times"""
     __implements__ = ObjectField.__implements__
@@ -1322,6 +1306,7 @@
     _properties.update({
         'type' : 'datetime',
         'widget' : CalendarWidget,
+        'size_significant' : True,
         })
 
     security  = ClassSecurityInfo()
@@ -1352,6 +1337,7 @@
         'type' : 'lines',
         'default' : (),
         'widget' : LinesWidget,
+        'size_significant' : True,
         })
 
     security  = ClassSecurityInfo()
@@ -1385,16 +1371,6 @@
     def getRaw(self, instance, **kwargs):
         return self.get(instance, **kwargs)
 
-    security.declarePublic('get_size')
-    def get_size(self, instance):
-        """Get size of the stored data used for get_size in BaseObject
-        """
-        size=0
-        for line in self.get(instance):
-            size+=len(str(line))
-        return size
-
-
 class IntegerField(ObjectField):
     """A field that stores an integer"""
     __implements__ = ObjectField.__implements__
@@ -1749,13 +1725,6 @@
         __traceback_info__ = (content_instance, self.getName(), pairs)
         return DisplayList(pairs)
 
-    security.declarePublic('get_size')
-    def get_size(self, instance):
-        """Get size of the stored data used for get_size in BaseObject
-        """
-        return 0
-
-
 class ComputedField(Field):
     """A field that stores a read-only computation."""
     __implements__ = Field.__implements__
@@ -1780,14 +1749,6 @@
         """Return the computed value."""
         return eval(self.expression, {'context': instance, 'here' : instance})
 
-    security.declarePublic('get_size')
-    def get_size(self, instance):
-        """Get size of the stored data.
-
-        Used for get_size in BaseObject.
-        """
-        return 0
-
 class BooleanField(ObjectField):
     """A field that stores boolean values."""
     __implements__ = ObjectField.__implements__
@@ -1811,12 +1772,6 @@
 
         ObjectField.set(self, instance, value, **kwargs)
 
-    security.declarePublic('get_size')
-    def get_size(self, instance):
-        """Get size of the stored data used for get_size in BaseObject
-        """
-        return True
-
 class CMFObjectField(ObjectField):
     """
     COMMENT TODO
@@ -1998,6 +1953,7 @@
         'widget': ImageWidget,
         'storage': AttributeStorage(),
         'content_class': Image,
+        'size_significant' : True,
         })
 
     security  = ClassSecurityInfo()
@@ -2272,18 +2228,19 @@
         """Get size of the stored data used for get_size in BaseObject
         """
         sizes = self.getAvailableSizes(instance)
-        original = self.get(instance)
-        size = original and original.get_size() or 0
-
+        size=0
+        storage=self.getStorage(instance)
+        if ISizeableStorage.isImplementedBy(storage):
+            size=storage.get_size(self.getName(), instance)
         if sizes:
             for name in sizes.keys():
                 id = self.getScaleName(scale=name)
                 try:
-                    data = self.getStorage(instance).get(id, instance)
+                    img_size = storage.get_size(id, instance)
                 except AttributeError:
                     pass
                 else:
-                    size+=data and data.get_size() or 0
+                    size+=img_size
         return size
 
     security.declareProtected(CMFCorePermissions.View, 'tag')
@@ -2587,6 +2544,7 @@
             },
         'widget': ImageWidget,
         'storage': AttributeStorage(),
+        'size_significant' : True,
         })
 
     security  = ClassSecurityInfo()
Index: Storage/__init__.py
===================================================================
--- Storage/__init__.py	(revision 4469)
+++ Storage/__init__.py	(working copy)
@@ -1,4 +1,4 @@
-from Products.Archetypes.interfaces.storage import IStorage
+from Products.Archetypes.interfaces.storage import IStorage,ISizeableStorage
 from Products.Archetypes.interfaces.layer import ILayer
 from Products.Archetypes.debug import log
 from Products.Archetypes.utils import shasattr
@@ -11,6 +11,8 @@
 from AccessControl import ClassSecurityInfo
 from Products.Archetypes.Registry import setSecurity, registerStorage
 
+from size import PlugableSizeStorage
+
 type_map = {'text':'string',
             'datetime':'date',
             'lines':'lines',
@@ -20,7 +22,7 @@
 _marker = []
 
 #XXX subclass from Base?
-class Storage:
+class Storage(PlugableSizeStorage):
     """Basic, abstract class for Storages. You need to implement
     at least those methods"""
 
@@ -89,7 +91,7 @@
     """Stores data as an attribute of the instance. This is the most
     commonly used storage"""
 
-    __implements__ = IStorage
+    __implements__ = IStorage,ISizeableStorage
 
     security = ClassSecurityInfo()
 
@@ -104,6 +106,7 @@
         # Remove acquisition wrappers
         value = aq_base(value)
         setattr(aq_base(instance), name, value)
+        self.set_size(name, instance, **kwargs)
         instance._p_changed = 1
 
     security.declarePrivate('unset')
@@ -118,7 +121,7 @@
     """Stores data using the Objectmanager interface. It's usually
     used for BaseFolder-based content"""
 
-    __implements__ = IStorage
+    __implements__ = IStorage,ISizeableStorage
 
     security = ClassSecurityInfo()
 
@@ -149,7 +152,7 @@
     """Storage used for ExtensibleMetadata. Attributes are stored on
     a persistent mapping named ``_md`` on the instance."""
 
-    __implements__ = IStorage, ILayer
+    __implements__ = IStorage, ILayer,ISizeableStorage
 
     security = ClassSecurityInfo()
 
@@ -187,6 +190,7 @@
 	            base._md=PersistentMapping()
 
         base._md[name] = aq_base(value)
+        self.set_size(name, instance, **kwargs)
         base._p_changed = 1
 
     security.declarePrivate('unset')

------=_NextPart_000_00B7_01C57585.D4158F10
Content-Type: text/plain; name="size.py"
Content-Disposition: attachment; filename="size.py"
Content-Transfer-Encoding: 8bit

from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.annotations import getAnnotation
from types import StringTypes,\
                  BooleanType,\
                  FloatType,\
                  IntType,\
                  NoneType,\
                  TupleType,\
                  ListType,\
                  LongType

from OFS.Image import File,Image

class PlugableSizeStorage:
    def get_size(self,name, instance, **kwargs):
        """Get the size from annotations storage"""
        aw=getAnnotation(instance)
        return aw.get(name,0)
    
    def set_size(self,name, instance, **kwargs):
        """get the size from data an cache it with annotations"""
        size=0
        aw=getAnnotation(instance)
        data=self.get(name, instance, **kwargs)
        if type(data) in StringTypes:
            size=len(data)
        elif isinstance(data, Image) or isinstance(data, File):
            size = data.get_size()
        elif IBaseUnit.isImplementedBy(data):
            size=len(data)
        elif type(data) in (ListType,TupleType):
            return len(''.join(data))
        elif type(data) in (BooleanType,FloatType,IntType,NoneType,LongType):
            size=0
        else:
            size=len(str(data))
        aw.set(name,size)

------=_NextPart_000_00B7_01C57585.D4158F10--
