#
# PloneTestCase
#

# $Id: ArchetypesTestCase.py,v 1.1.2.1 2003/10/20 17:09:17 tiran Exp $

from Testing import ZopeTestCase

ZopeTestCase.installProduct('CMFCore')
ZopeTestCase.installProduct('CMFDefault')
ZopeTestCase.installProduct('CMFCalendar')
ZopeTestCase.installProduct('CMFTopic')
ZopeTestCase.installProduct('DCWorkflow')
ZopeTestCase.installProduct('MailHost', quiet=1)
ZopeTestCase.installProduct('PageTemplates', quiet=1)
ZopeTestCase.installProduct('PythonScripts', quiet=1)
ZopeTestCase.installProduct('ExternalMethod', quiet=1) 
ZopeTestCase.installProduct('Archetypes')
ZopeTestCase.installProduct('PortalTransforms')

class ArchetypesTestCase(ZopeTestCase.ZopeTestCase):
    pass    
