#
# ArchetypesTestCase
#
# $Id: ArchetypesTestCase.py,v 1.6 2004/05/28 16:12:14 tiran Exp $

from Testing import ZopeTestCase

ZopeTestCase.installProduct('CMFCore', 1)
ZopeTestCase.installProduct('CMFDefault', 1)
ZopeTestCase.installProduct('CMFCalendar', 1)
ZopeTestCase.installProduct('CMFTopic', 1)
ZopeTestCase.installProduct('DCWorkflow', 1)
ZopeTestCase.installProduct('CMFActionIcons', 1)
ZopeTestCase.installProduct('CMFQuickInstallerTool', 1)
ZopeTestCase.installProduct('CMFFormController', 1)
ZopeTestCase.installProduct('GroupUserFolder', 1)
ZopeTestCase.installProduct('ZCTextIndex', 1)
ZopeTestCase.installProduct('CMFPlone', 1)
ZopeTestCase.installProduct('MailHost', quiet=1)
ZopeTestCase.installProduct('PageTemplates', quiet=1)
ZopeTestCase.installProduct('PythonScripts', quiet=1)
ZopeTestCase.installProduct('ExternalMethod', quiet=1)
ZopeTestCase.installProduct('ZCatalog', 1)
ZopeTestCase.installProduct('MimetypesRegistry', 1)
ZopeTestCase.installProduct('PortalTransforms', 1)
ZopeTestCase.installProduct('Archetypes', 1)
ZopeTestCase.installProduct('ArchExample', 1)
ZopeTestCase.installProduct('ArchetypesTestUpdateSchema', 1)

class ArchetypesTestCase(ZopeTestCase.ZopeTestCase):
    pass
