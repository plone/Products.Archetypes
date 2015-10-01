from Products.CMFCore.utils import getToolByName

from Products.Archetypes.tests.attestcase import ATTestCase
from Products.Archetypes.tests.utils import makeContent


class RefSpeedupTestMixin:

    def afterSetUp(self):
        self.rc = getToolByName(self.portal, 'reference_catalog')
        self.loginAsPortalOwner()
        self.doc1 = makeContent(
            self.portal, portal_type='DDocument', id='doc1')
        self.doc2 = makeContent(
            self.portal, portal_type='DDocument', id='doc2')
        self.doc3 = makeContent(
            self.portal, portal_type='DDocument', id='doc3')


class TestGetReferences(RefSpeedupTestMixin, ATTestCase):

    def test_none(self):
        self.assertEqual(self.rc.getReferences(self.doc1), [])
        self.assertEqual(self.rc.getReferences(self.doc1, 'related'), [])
        self.assertEqual(self.rc.getReferences(
            self.doc1, 'related', self.doc2), [])

        result = self.rc.getReferences(self.doc1, ['related', 'rel2'])
        self.assertEqual(result, [])
        result = self.rc.getReferences(
            self.doc1, ['related', 'rel2'], self.doc2)
        self.assertEqual(result, [])

        self.assertEqual(self.doc1.getReferences(), [])

    def test_single(self):
        self.doc1.setRelated([self.doc2.UID()])
        result = self.rc.getReferences(self.doc1)
        self.assertEqual(result[0].getTargetObject(), self.doc2)
        result = self.rc.getReferences(self.doc1, 'related')
        self.assertEqual(result[0].getTargetObject(), self.doc2)
        result = self.rc.getReferences(self.doc1, 'related', self.doc2)
        self.assertEqual(result[0].getTargetObject(), self.doc2)
        result = self.rc.getReferences(self.doc1, 'related', self.doc3)
        self.assertEqual(result, [])

        self.assertEqual(self.doc1.getReferences()[0], self.doc2)

        self.doc1.setRel2([self.doc3.UID()])
        result = self.rc.getReferences(self.doc1, ['related', 'rel2'])
        result = [r.getTargetObject() for r in result]
        self.assertEqual(set(result), set([self.doc2, self.doc3]))

        result = self.rc.getReferences(
            self.doc1, ['related', 'rel2'], self.doc2)
        result = [r.getTargetObject() for r in result]
        self.assertEqual(set(result), set([self.doc2]))

    def test_many(self):
        uids = [self.doc2.UID(), self.doc3.UID()]
        self.doc1.setRelated(uids)
        result = [r.getTargetObject()
                  for r in self.rc.getReferences(self.doc1)]
        self.assertEqual(set(result), set([self.doc2, self.doc3]))

        self.assertEqual(set(self.doc1.getReferences()),
                         set([self.doc2, self.doc3]))

        self.doc1.setRel2([self.doc2.UID()])
        result = self.rc.getReferences(self.doc1, ['related', 'rel2'])
        result = [r.getTargetObject() for r in result]
        self.assertEqual(set(result), set([self.doc2, self.doc3]))

    def test_bidi(self):
        self.doc1.setRelated([self.doc2.UID()])
        self.doc2.setRelated([self.doc1.UID()])
        result = [r.getTargetObject()
                  for r in self.rc.getReferences(self.doc1)]
        self.assertEqual(result, [self.doc2])
        result = [r.getTargetObject()
                  for r in self.rc.getReferences(self.doc2)]
        self.assertEqual(result, [self.doc1])

        self.doc1.setRel2([self.doc3.UID()])
        result = self.rc.getReferences(self.doc1, ['related', 'rel2'])
        result = [r.getTargetObject() for r in result]
        self.assertEqual(set(result), set([self.doc2, self.doc3]))

    def test_missing_uid_catalog_entry(self):
        self.doc1.setRelated([self.doc2.UID()])

        result = [r.getTargetObject()
                  for r in self.rc.getReferences(self.doc1)]
        self.assertEqual(result, [self.doc2])

        # Forcefully remove the target object from the uid catalog
        uc = getToolByName(self.portal, 'uid_catalog')
        uc.uncatalog_object(self.doc2._getURL())

        references = self.rc.getReferences(self.doc1)
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0].getTargetObject(), None)


class TestGetBackReferences(RefSpeedupTestMixin, ATTestCase):

    def test_none(self):
        self.assertEqual(self.rc.getBackReferences(self.doc1), [])
        self.assertEqual(self.rc.getBackReferences(self.doc1, 'related'), [])
        self.assertEqual(self.rc.getBackReferences(self.doc1, 'related', self.doc2),
                         [])

        result = self.rc.getBackReferences(self.doc1, ['related', 'rel2'])
        self.assertEqual(result, [])
        result = self.rc.getBackReferences(
            self.doc1, ['related', 'rel2'], self.doc2)
        self.assertEqual(result, [])

        self.assertEqual(self.doc1.getBackReferences(), [])

    def test_single(self):
        self.doc1.setRelated([self.doc2.UID()])

        result = self.rc.getBackReferences(self.doc2)
        self.assertEqual(result[0].getSourceObject(), self.doc1)
        result = self.rc.getBackReferences(self.doc2, 'related')
        self.assertEqual(result[0].getSourceObject(), self.doc1)
        result = self.rc.getBackReferences(self.doc2, 'related', self.doc1)
        self.assertEqual(result[0].getSourceObject(), self.doc1)
        result = self.rc.getBackReferences(self.doc2, 'related', self.doc3)
        self.assertEqual(result, [])

        self.assertEqual(self.doc2.getBackReferences('related')[0], self.doc1)

        self.doc1.setRel2([self.doc3.UID()])
        result = self.rc.getBackReferences(self.doc2, ['related', 'rel2'])
        self.assertEqual(result[0].getSourceObject(), self.doc1)
        result = self.rc.getBackReferences(
            self.doc2, ['related', 'rel2'], self.doc1)
        self.assertEqual(result[0].getSourceObject(), self.doc1)

    def test_many(self):
        uids = [self.doc2.UID(), self.doc3.UID()]
        self.doc1.setRelated(uids)

        result = [r.getSourceObject()
                  for r in self.rc.getBackReferences(self.doc2)]
        self.assertEqual(set(result), set([self.doc1]))
        result = [r.getSourceObject()
                  for r in self.rc.getBackReferences(self.doc3)]
        self.assertEqual(set(result), set([self.doc1]))

        self.assertEqual(set(self.doc2.getBackReferences()), set([self.doc1]))

        uids2 = [self.doc1.UID(), self.doc2.UID()]
        self.doc3.setRel2(uids2)
        result = self.rc.getBackReferences(self.doc2, ['related', 'rel2'])
        result = [r.getSourceObject() for r in result]
        self.assertEqual(set(result), set([self.doc1, self.doc3]))

    def test_bidi(self):
        self.doc1.setRelated([self.doc2.UID()])
        self.doc2.setRelated([self.doc1.UID()])

        result = [r.getSourceObject()
                  for r in self.rc.getBackReferences(self.doc1)]
        self.assertEqual(result, [self.doc2])
        result = [r.getSourceObject()
                  for r in self.rc.getBackReferences(self.doc2)]
        self.assertEqual(result, [self.doc1])

        self.doc2.setRel2([self.doc1.UID()])
        result = self.rc.getBackReferences(self.doc2, ['related', 'rel2'])
        result = [r.getSourceObject() for r in result]
        self.assertEqual(set(result), set([self.doc1]))

    def test_missing_uid_catalog_entry(self):
        self.doc2.setRelated([self.doc1.UID()])

        result = [r.getSourceObject()
                  for r in self.rc.getBackReferences(self.doc1)]
        self.assertEqual(result, [self.doc2])

        # Forcefully remove the target object from the uid catalog
        uc = getToolByName(self.portal, 'uid_catalog')
        uc.uncatalog_object(self.doc2._getURL())

        references = self.rc.getBackReferences(self.doc1)
        self.assertEqual(len(references), 1)
        self.assertEqual(references[0].getSourceObject(), None)


class TestReferenceable(RefSpeedupTestMixin, ATTestCase):

    def test_no_references(self):
        self.assertEqual(self.doc1.getRelated(), [])
        self.assertEqual(self.doc1.getRawRelated(), [])
        self.assertEqual(self.doc1.getReferences(), [])
        self.assertEqual(self.doc1.getRelationships(), [])

    def test_single_reference(self):
        self.doc1.setRelated([self.doc2.UID()])
        self.assertEqual(self.doc1.getRelated(), [self.doc2])
        self.assertEqual(self.doc1.getRawRelated(), [self.doc2.UID()])
        self.assertEqual(self.doc1.getReferences(), [self.doc2])
        self.assertEqual(self.doc1.getRelationships(), ['related'])

    def test_many_references(self):
        uids = [self.doc2.UID(), self.doc3.UID()]
        self.doc1.setRelated(uids)
        self.assertEqual(set(self.doc1.getRelated()),
                         set([self.doc2, self.doc3]))
        self.assertEqual(set(self.doc1.getRawRelated()), set(uids))
        self.assertEqual(set(self.doc1.getReferences()),
                         set([self.doc2, self.doc3]))
        self.assertEqual(self.doc1.getRelationships(), ['related'])

    def test_bidi_references(self):
        self.doc1.setRelated([self.doc2.UID()])
        self.doc2.setRelated([self.doc1.UID()])
        self.assertEqual(self.doc1.getRelated(), [self.doc2])
        self.assertEqual(self.doc1.getRawRelated(), [self.doc2.UID()])
        self.assertEqual(self.doc1.getReferences(), [self.doc2])
        self.assertEqual(self.doc1.getRelationships(), ['related'])
        self.assertEqual(self.doc2.getRelated(), [self.doc1])
        self.assertEqual(self.doc2.getRawRelated(), [self.doc1.UID()])
        self.assertEqual(self.doc2.getReferences(), [self.doc1])
        self.assertEqual(self.doc2.getRelationships(), ['related'])
