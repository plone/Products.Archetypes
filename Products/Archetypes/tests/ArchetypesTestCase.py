#
# ArchetypesTestCase
#

# $Id: ArchetypesTestCase.py,v 1.3 2003/11/03 22:05:22 dreamcatcher Exp $

from Testing import ZopeTestCase

ZopeTestCase.installProduct('CMFCore')
ZopeTestCase.installProduct('CMFDefault')
ZopeTestCase.installProduct('CMFCalendar')
ZopeTestCase.installProduct('CMFTopic')
ZopeTestCase.installProduct('DCWorkflow')
ZopeTestCase.installProduct('CMFActionIcons')
ZopeTestCase.installProduct('CMFQuickInstallerTool')
ZopeTestCase.installProduct('CMFFormController')
ZopeTestCase.installProduct('GroupUserFolder')
ZopeTestCase.installProduct('ZCTextIndex')
ZopeTestCase.installProduct('CMFPlone')
ZopeTestCase.installProduct('MailHost', quiet=1)
ZopeTestCase.installProduct('PageTemplates', quiet=1)
ZopeTestCase.installProduct('PythonScripts', quiet=1)
ZopeTestCase.installProduct('ExternalMethod', quiet=1)
ZopeTestCase.installProduct('ZCatalog')
ZopeTestCase.installProduct('Archetypes')
ZopeTestCase.installProduct('ArchetypesTestUpdateSchema')
ZopeTestCase.installProduct('PortalTransforms')

class ArchetypesTestCase(ZopeTestCase.ZopeTestCase):
    pass
