"""
Unittests for a Schema Provider

$Id: test_schemaProvider.py,v 1.1.2.8 2004/04/20 04:43:36 bcsaller Exp $
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
from Products.Archetypes.Schema.Collection import getAxisManagers

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
        for axis in getAxisManagers():
            at.registerSchemaAxis(axis)

        pmap = {
            'instance' : 0,
            'portal_type' : 1,
            "containment": 2,
            'reference' : 3,
            }
        # now assign these priorities to the policy
        p = at._getPolicyMemento("archetype_policy")
        p.update(pmap)



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

        assert objb.Schema() == DDocumentSchema

        # Now we need to make folder a provider of a new Schemata
        # and assert those fields appear on objb
        f = TextField('newField')
        testSchema = Schema ((f,))

        at.provideSchema('containment', instance=folder, schema=testSchema)

        g = objb.Schema()['newField']
        assert g.type == "text"
        assert g.getName() == f.getName()
        # Assert something about the priority
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


        a = TextField('FieldA')
        b = TextField('FieldB')
        testSchemaA = Schema ((a,))
        testSchemaB = Schema ((b,))

        at.provideSchema('reference', instance=objb, source=folder,
                   schema=testSchemaA)
        at.provideSchema('reference', instance=objb, source=obja,
                   schema=testSchemaB)

        schema = objb.Schema()
        assert schema['FieldA']
        assert schema['FieldB']



    def testChainedProviders(self):
        site = self.getPortal()
        at = site.archetype_tool
        # The torture test
        # Build a tree
        # x (p ref s,t) -> y(p aq SchemaY) -> z(p aq Schema Z) -> Document(i aq)
        # s (p - SchemaS)
        # t (p - SchemaT)
        # The older collector model included x.s, x.t in i's schema,
        # this was wrong, because it traversed axes. A policy could do
        # this by doing aq walks and collecting schema on other axes,
        # but this will not be the default

        x = makeContent(site, "SimpleFolder", 'x')
        y = makeContent(x, "SimpleFolder", 'y')
        z = makeContent(y, "SimpleFolder", 'z')
        i = makeContent(z, "DDocument", 'i')
        s = makeContent(site, "DDocument", 's')
        t = makeContent(site, "DDocument", 't')

        SchemaS = Schema((TextField('FieldS'),))
        SchemaT = Schema((TextField('FieldT'),))

        at.provideSchema('reference', instance=x, source=s,
                         schema=SchemaS)
        at.provideSchema('reference', instance=x, source=t,
                         schema=SchemaT)

        SchemaY = Schema((TextField('FieldY'),))
        at.provideSchema('containment', instance=y, schema=SchemaY)

        SchemaZ = Schema((TextField('FieldZ'),))
        at.provideSchema('containment', instance=z, schema=SchemaZ)

        ## then assert that schema == i + z + y + s + t (DEPRECATED)
        ## now we expect i + y + z
        schema = i.Schema()
        expected = DDocumentSchema + SchemaY + SchemaZ
        assert schema == expected

        # assert that we can still tell where these fields come from
        assert schema['FieldY'].provider == ('containment', y.UID())
        assert schema['FieldZ'].provider == ('containment', z.UID())


    def test_TypeCollector(self):
        site = self.getPortal()
        at = site.archetype_tool
        x = makeContent(site, "SimpleFolder", 'x')
        y = makeContent(site, "DDocument", 'y')
        z = makeContent(site, "SimpleType", 'z')

        SchemaA = Schema((TextField('FieldA'),))


        at.provideSchema('portal_type', portal_type=z.portal_type, schema=SchemaA)

        assert y.Schema() == DDocumentSchema
        assert z.Schema()['FieldA']


    def test_Editor(self):
        site = self.getPortal()
        at = site.archetype_tool
        x = makeContent(site, "SimpleFolder", 'x')
        z = makeContent(site, "SimpleType", 'z')

        SchemaA = Schema((TextField('FieldA'),))

        at.provideSchema('portal_type', portal_type=z.portal_type, schema=SchemaA)
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
        at.provideSchema('containment', instance=x, schema=SchemaA)

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
