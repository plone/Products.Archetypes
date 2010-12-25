from Products.CMFCore.utils import getToolByName

from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent


class ATRefSpeedupTestCase(ATSiteTestCase):

    def afterSetUp(self):
        self.rc = getToolByName(self.portal, 'reference_catalog')
        self.loginAsPortalOwner()
        makeContent(self.portal, portal_type='DDocument', id='doc1')
        makeContent(self.portal, portal_type='DDocument', id='doc2')
        makeContent(self.portal, portal_type='DDocument', id='doc3')


class TestGetReferences(ATRefSpeedupTestCase):

    def test_none(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        self.assertEquals(self.rc.getReferences(doc1), [])
        self.assertEquals(self.rc.getReferences(doc1, 'related'), [])
        self.assertEquals(self.rc.getReferences(doc1, 'related', doc2), [])

        result = self.rc.getReferences(doc1, ['related', 'rel2'])
        self.assertEquals(result, [])
        result = self.rc.getReferences(doc1, ['related', 'rel2'], doc2)
        self.assertEquals(result, [])

        self.assertEquals(doc1.getReferences(), [])

    def test_single(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc3 = self.portal.doc3
        doc1.setRelated([doc2.UID()])
        result = self.rc.getReferences(doc1)
        self.assertEquals(result[0].getTargetObject(), doc2)
        result = self.rc.getReferences(doc1, 'related')
        self.assertEquals(result[0].getTargetObject(), doc2)
        result = self.rc.getReferences(doc1, 'related', doc2)
        self.assertEquals(result[0].getTargetObject(), doc2)
        result = self.rc.getReferences(doc1, 'related', doc3)
        self.assertEquals(result, [])

        self.assertEquals(doc1.getReferences()[0], doc2)

        doc1.setRel2([doc3.UID()])
        result = self.rc.getReferences(doc1, ['related', 'rel2'])
        result = [r.getTargetObject() for r in result]
        self.assertEquals(set(result), set([doc2, doc3]))

        result = self.rc.getReferences(doc1, ['related', 'rel2'], doc2)
        result = [r.getTargetObject() for r in result]
        self.assertEquals(set(result), set([doc2]))

    def test_many(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc3 = self.portal.doc3
        uids = [doc2.UID(), doc3.UID()]
        doc1.setRelated(uids)
        result = [r.getTargetObject() for r in self.rc.getReferences(doc1)]
        self.assertEquals(set(result), set([doc2, doc3]))

        self.assertEquals(set(doc1.getReferences()), set([doc2, doc3]))

        doc1.setRel2([doc2.UID()])
        result = self.rc.getReferences(doc1, ['related', 'rel2'])
        result = [r.getTargetObject() for r in result]
        self.assertEquals(set(result), set([doc2, doc3]))

    def test_bidi(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc3 = self.portal.doc3
        doc1.setRelated([doc2.UID()])
        doc2.setRelated([doc1.UID()])
        result = [r.getTargetObject() for r in self.rc.getReferences(doc1)]
        self.assertEquals(result, [doc2])
        result = [r.getTargetObject() for r in self.rc.getReferences(doc2)]
        self.assertEquals(result, [doc1])

        doc1.setRel2([doc3.UID()])
        result = self.rc.getReferences(doc1, ['related', 'rel2'])
        result = [r.getTargetObject() for r in result]
        self.assertEquals(set(result), set([doc2, doc3]))

    def test_missing_uid_catalog_entry(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc1.setRelated([doc2.UID()])

        result = [r.getTargetObject() for r in self.rc.getReferences(doc1)]
        self.assertEquals(result, [doc2])

        # Forcefully remove the target object from the uid catalog
        uc = getToolByName(self.portal, 'uid_catalog')
        uc.uncatalog_object(doc2._getURL())

        references = self.rc.getReferences(doc1)
        self.assertEquals(len(references), 1)
        self.assertEquals(references[0].getTargetObject(), None)


class TestGetBackReferences(ATRefSpeedupTestCase):

    def test_none(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        self.assertEquals(self.rc.getBackReferences(doc1), [])
        self.assertEquals(self.rc.getBackReferences(doc1, 'related'), [])
        self.assertEquals(self.rc.getBackReferences(doc1, 'related', doc2),
                          [])

        result = self.rc.getBackReferences(doc1, ['related', 'rel2'])
        self.assertEquals(result, [])
        result = self.rc.getBackReferences(doc1, ['related', 'rel2'], doc2)
        self.assertEquals(result, [])

        self.assertEquals(doc1.getBackReferences(), [])

    def test_single(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc3 = self.portal.doc3
        doc1.setRelated([doc2.UID()])

        result = self.rc.getBackReferences(doc2)
        self.assertEquals(result[0].getSourceObject(), doc1)
        result = self.rc.getBackReferences(doc2, 'related')
        self.assertEquals(result[0].getSourceObject(), doc1)
        result = self.rc.getBackReferences(doc2, 'related', doc1)
        self.assertEquals(result[0].getSourceObject(), doc1)
        result = self.rc.getBackReferences(doc2, 'related', doc3)
        self.assertEquals(result, [])

        self.assertEquals(doc2.getBackReferences('related')[0], doc1)

        doc1.setRel2([doc3.UID()])
        result = self.rc.getBackReferences(doc2, ['related', 'rel2'])
        self.assertEquals(result[0].getSourceObject(), doc1)
        result = self.rc.getBackReferences(doc2, ['related', 'rel2'], doc1)
        self.assertEquals(result[0].getSourceObject(), doc1)

    def test_many(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc3 = self.portal.doc3
        uids = [doc2.UID(), doc3.UID()]
        doc1.setRelated(uids)

        result = [r.getSourceObject() for r in self.rc.getBackReferences(doc2)]
        self.assertEquals(set(result), set([doc1]))
        result = [r.getSourceObject() for r in self.rc.getBackReferences(doc3)]
        self.assertEquals(set(result), set([doc1]))

        self.assertEquals(set(doc2.getBackReferences()), set([doc1]))

        uids2 = [doc1.UID(), doc2.UID()]
        doc3.setRel2(uids2)
        result = self.rc.getBackReferences(doc2, ['related', 'rel2'])
        result = [r.getSourceObject() for r in result]
        self.assertEquals(set(result), set([doc1, doc3]))

    def test_bidi(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc1.setRelated([doc2.UID()])
        doc2.setRelated([doc1.UID()])

        result = [r.getSourceObject() for r in self.rc.getBackReferences(doc1)]
        self.assertEquals(result, [doc2])
        result = [r.getSourceObject() for r in self.rc.getBackReferences(doc2)]
        self.assertEquals(result, [doc1])

        doc2.setRel2([doc1.UID()])
        result = self.rc.getBackReferences(doc2, ['related', 'rel2'])
        result = [r.getSourceObject() for r in result]
        self.assertEquals(set(result), set([doc1]))

    def test_missing_uid_catalog_entry(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc2.setRelated([doc1.UID()])

        result = [r.getSourceObject() for r in self.rc.getBackReferences(doc1)]
        self.assertEquals(result, [doc2])

        # Forcefully remove the target object from the uid catalog
        uc = getToolByName(self.portal, 'uid_catalog')
        uc.uncatalog_object(doc2._getURL())

        references = self.rc.getBackReferences(doc1)
        self.assertEquals(len(references), 1)
        self.assertEquals(references[0].getSourceObject(), None)


class TestReferenceable(ATRefSpeedupTestCase):

    def test_no_references(self):
        doc1 = self.portal.doc1
        self.assertEquals(doc1.getRelated(), [])
        self.assertEquals(doc1.getRawRelated(), [])
        self.assertEquals(doc1.getReferences(), [])
        self.assertEquals(doc1.getRelationships(), [])

    def test_single_reference(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc1.setRelated([doc2.UID()])
        self.assertEquals(doc1.getRelated(), [doc2])
        self.assertEquals(doc1.getRawRelated(), [doc2.UID()])
        self.assertEquals(doc1.getReferences(), [doc2])
        self.assertEquals(doc1.getRelationships(), ['related'])

    def test_many_references(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc3 = self.portal.doc3
        uids = [doc2.UID(), doc3.UID()]
        doc1.setRelated(uids)
        self.assertEquals(set(doc1.getRelated()), set([doc2, doc3]))
        self.assertEquals(set(doc1.getRawRelated()), set(uids))
        self.assertEquals(set(doc1.getReferences()), set([doc2, doc3]))
        self.assertEquals(doc1.getRelationships(), ['related'])

    def test_bidi_references(self):
        doc1 = self.portal.doc1
        doc2 = self.portal.doc2
        doc1.setRelated([doc2.UID()])
        doc2.setRelated([doc1.UID()])
        self.assertEquals(doc1.getRelated(), [doc2])
        self.assertEquals(doc1.getRawRelated(), [doc2.UID()])
        self.assertEquals(doc1.getReferences(), [doc2])
        self.assertEquals(doc1.getRelationships(), ['related'])
        self.assertEquals(doc2.getRelated(), [doc1])
        self.assertEquals(doc2.getRawRelated(), [doc1.UID()])
        self.assertEquals(doc2.getReferences(), [doc1])
        self.assertEquals(doc2.getRelationships(), ['related'])


def test_suite():
    from unittest import TestSuite, makeSuite
    suite = TestSuite()
    suite.addTest(makeSuite(TestGetReferences))
    suite.addTest(makeSuite(TestGetBackReferences))
    suite.addTest(makeSuite(TestReferenceable))
    return suite
