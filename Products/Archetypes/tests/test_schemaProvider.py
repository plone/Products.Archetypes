"""
Unittests for a Schema Provider

$Id: test_schemaProvider.py,v 1.1.2.7 2004/04/14 20:37:56 bcsaller Exp $
"""

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import *
from utils import *

from Acquisition import aq_base
import Products.Archetypes.config as config
from Products.Archetypes.public import *
from Products.Archetypes.examples.DDocument import schema as DDocumentSchema
from Products.Archetypes.SchemaProvider import *


class MementoTool:
    def __init__(self):
        self.storage = {}
        
    def setMemento(self, instance, memento):
        uid = instance.UID()
        self.storage[uid] = memento

    def getMemento(self, instance):
        uid = instance.UID()
        return self.storage.get(uid)
    

class SchemaProviderTests(ArcheSiteTestCase):
    def afterSetUp(self):
        ArcheSiteTestCase.afterSetUp(self)
        user = self.getManagerUser()
        newSecurityManager(None, user)
        self.init_collectors()

    def init_collectors(self):
        site = self.getPortal()
        at = site.archetype_tool
        at.registerSchemaCollector(SelfCollector())
        at.registerSchemaCollector(TypeCollector())
        at.registerSchemaCollector(AcquisitionCollector())
        at.registerSchemaCollector(ReferenceCollector())
        
    def test_singleSchemaTest(self):
        # Test that the baseline get Schema Continues to Function
        # When no schema collector is associated with the object
        # (and hence no providers)
        site = self.getPortal()
        obja = makeContent(site, "DDocument", "obja")
        objb = makeContent(site, "SimpleType", "objb")
        
        assert obja.Schema() == DDocumentSchema
        assert objb.Schema() != DDocumentSchema

    def test_aqCollector(self):
        site = self.getPortal()
        at = site.archetype_tool
        
        folder = makeContent(site, "SimpleFolder", "folder")
        objb = makeContent(folder, "DDocument", "objb")

        #Lets say that folder is a schema provider for objB
        # (but in this case provides nothing)
        objb.setSchemaCollector('acquisition')
        assert objb.Schema() == DDocumentSchema
        
        # Now we need to make folder a provider of a new Schemata
        # and assert those fields appear on objb
        f = TextField('newField')
        testSchema = Schema ((f,))
        
        at.provideSchema(folder, testSchema)
        folder.setSchemaPriority(11) # low low pri
        g = objb.Schema()['newField']
        assert g.type == "text"
        assert g.getName() == f.getName()
        assert g is objb.Schema().fields()[-1]
        mutator = g.getMutator(objb)
        accessor = g.getAccessor(objb)

        mutator("monkey")
        assert accessor() == "monkey"

        objb = site.folder.objb
        g = objb.Schema()['newField']
        mutator = g.getMutator(objb)
        accessor = g.getAccessor(objb)
        mutator("monkey")
        assert accessor() == "monkey"

        objb.set('newField', 'butter')
        assert objb.get('newField') == "butter"

    def testReferenceCollector(self):
        site = self.getPortal()
        at = site.archetype_tool
        
        folder = makeContent(site, "SimpleFolder", "folder")
        obja = makeContent(folder, "DDocument", "obja")
        objb = makeContent(folder, "DDocument", "objb")

        objb.setSchemaCollector('reference')

        a = TextField('FieldA')
        b = TextField('FieldB')
        testSchemaA = Schema ((a,))
        testSchemaB = Schema ((b,))

        folder.setSchemaPriority(11) # low low pri
        obja.setSchemaPriority(12) # and lower still pri

        at.provideSchema(folder, testSchemaA)
        at.provideSchema(obja, testSchemaB)

        objb.addReference(folder, relationship='schema_provider')
        objb.addReference(obja, relationship='schema_provider')
        
        schema = objb.Schema()
        assert schema.fields()[-2].getName() ==  a.getName()
        assert schema.fields()[-1].getName() ==  b.getName()
        

    def testChainedProviders(self):
        site = self.getPortal()
        at = site.archetype_tool
        # The torture test
        # Build a tree
        # x (p ref s,t) -> y(p aq SchemaY) -> z(p aq Schema Z) -> Document(i aq)
        # s (p - SchemaS)
        # t (p - SchemaT)
        
        x = makeContent(site, "SimpleFolder", 'x')
        y = makeContent(x, "SimpleFolder", 'y')
        z = makeContent(y, "SimpleFolder", 'z')
        i = makeContent(z, "DDocument", 'i')
        s = makeContent(site, "DDocument", 's')
        t = makeContent(site, "DDocument", 't')
        
        x.addReference(s, relationship="schema_provider")
        x.addReference(t, relationship="schema_provider")
        
        SchemaS = Schema((TextField('FieldS'),))
        SchemaT = Schema((TextField('FieldT'),))
        at.provideSchema(s, SchemaS)
        at.provideSchema(t, SchemaT)

        SchemaY = Schema((TextField('FieldY'),))
        at.provideSchema(y, SchemaY)

        SchemaZ = Schema((TextField('FieldZ'),))
        at.provideSchema(z, SchemaZ)

        x.setSchemaCollector('reference')
        y.setSchemaCollector('acquisition')
        z.setSchemaCollector('acquisition')
        i.setSchemaCollector('acquisition')

        i.setSchemaPriority(1)
        z.setSchemaPriority(2)
        y.setSchemaPriority(3)
        x.setSchemaPriority(4)
        s.setSchemaPriority(5)
        t.setSchemaPriority(6)
        
        # then assert that schema == i + z + y + s + t
        schema = i.Schema()
        expected = DDocumentSchema + SchemaZ + SchemaY + SchemaS + SchemaT
        assert schema == expected

        # assert that we can still tell where these fields come from
        assert schema['FieldY'].provider == y.UID()
        assert schema['FieldZ'].provider == z.UID()

        providers = i.getSchemaProviders()
        assert y in providers
        assert z in providers

    def test_TypeCollector(self):
        site = self.getPortal()
        at = site.archetype_tool
        x = makeContent(site, "SimpleFolder", 'x')
        y = makeContent(site, "DDocument", 'y')
        z = makeContent(site, "SimpleType", 'z')

        SchemaA = Schema((TextField('FieldA'),))
        at.provideSchema(z.meta_type, SchemaA)
        z.setSchemaCollector('type')
        
        assert y.Schema() == DDocumentSchema
        assert z.Schema()['FieldA']


    def test_Editor(self):
        site = self.getPortal()
        at = site.archetype_tool
        x = makeContent(site, "SimpleFolder", 'x')
        z = makeContent(site, "SimpleType", 'z')

        SchemaA = Schema((TextField('FieldA'),))
        at.provideSchema(z.meta_type, SchemaA)
        z.setSchemaCollector('type')

        # Z now has our new schema, this important
        # because we want to TTW add additional fields
        # to SchemaA
        se = z.getSchemaEditor()
        sse = se.getSchemaEditorForSubSchema('FieldA')
        assert sse.schema == SchemaA

        # This is a sub test of the memento storage up top...
        # and the ability to reassign the storage on the
        # subschema and have it work
        mt = MementoTool()
        ms = MementoStorage(mt)
        sse.assignStorage(ms)
        field = z.Schema()['FieldA']
        accessor = field.getAccessor(z)
        mutator = field.getMutator(z)
        mutator('monkeybutter')
        assert accessor() == 'monkeybutter'
        assert str(mt.storage[z.UID()]['FieldA']) == 'monkeybutter'

    def test_FormProcessing(self):
        site = self.getPortal()
        at = site.archetype_tool
        x = makeContent(site, "SimpleFolder", 'x')
        z = makeContent(x, "SimpleType", 'z')
        
        SchemaA = Schema((TextField('FieldA',
                                    default="fofofo",
                                    widget=StringWidget(description="desc",
                                                        label="label")),))
        at.provideSchema(x, SchemaA)
        z.setSchemaCollector('acquisition')

        schema = z.Schema()
        assert schema['FieldA']

        se = z.getSchemaEditor()
        # we want to test that with the correct form data we would mutate fieldA to something
        # different
        #set a value into FieldA
        f = schema['FieldA']
        f.getMutator(z)('lard')

        data = {
            'FieldA_ftype' : 'Products.Archetypes.Field.StringField',
            'FieldA_wtype' : 'Products.Archetypes.Widget.EpozWidget',
            }
        se.process_form(data)
        f = schema['FieldA']

        assert str(z.get('FieldA')) == 'lard'
        assert f.widget.Label(z) == 'label'
        assert f.widget.Description(z) == 'desc'


##    def testTypeProvider(self):
##        site = self.getPortal()
##        at = site.archetype_tool
##        x = makeContent(site, "SimpleType", 'x')
##        y = makeContent(site, "SimpleType", 'y')
        
##        SchemaA = Schema((TextField('FieldA',
##                                    default="fofofo",
##                                    widget=StringWidget(description="desc",
##                                                        label="label")),))
##        at.provideSchema(x, SchemaA)
##        x.setSchemaCollector('acquisition')
        
        
if __name__ == '__main__':
    framework()
else:
    # While framework.py provides its own test_suite()
    # method the testrunner utility does not.
    import unittest
    def test_suite():
        suite = unittest.TestSuite()
        suite.addTest(unittest.makeSuite(SchemaProviderTests))
        return suite
