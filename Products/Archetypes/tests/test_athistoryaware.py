import os
import shutil
import tempfile
import unittest

import Acquisition
import BTrees
import transaction
import OFS
import persistent
import ZODB
from ZODB.FileStorage import FileStorage

from Products.Archetypes.annotations import AT_ANN_STORAGE
from Products.Archetypes.athistoryaware import ATHistoryAwareMixin

KEY1 = AT_ANN_STORAGE + '-monty'
KEY2 = AT_ANN_STORAGE + '-python'
KEY3 = AT_ANN_STORAGE + '-lumberjack'

class DummyAnnotation(persistent.Persistent):
    spam = 'eggs'

class DummyObject(Acquisition.Implicit, persistent.Persistent,
                  ATHistoryAwareMixin):
    foo = 'bar'

    def __init__(self):
        annotations = BTrees.OOBTree.OOBTree()
        annotations[KEY1] = DummyAnnotation()
        annotations[KEY2] = DummyAnnotation()
        setattr(self, '__annotations__', annotations)

class ATHistoryAwareTests(unittest.TestCase):
    def setUp(self):
        # Set up a ZODB and Application object. We can't use DemoStorage
        # as it doesn't support the history() API.
        self._dir = tempfile.mkdtemp()
        self._storage = FileStorage(
            os.path.join(self._dir,'test_athistoryaware.fs'),
            create=True)
        self._connection = ZODB.DB(self._storage).open()
        root = self._connection.root()
        root['Application'] = OFS.Application.Application()
        self.app = root['Application']

        # Our basic testing object
        self.app.object = DummyObject()
        self.object = self.app.object
        t = transaction.get()
        t.description = None # clear initial transaction note
        t.note('Transaction 1')
        t.setUser('User 1')
        t.commit()

        # Alter object and annotations over several transactions
        annotations = self.object.__annotations__
        self.object.foo = 'baz'
        annotations[KEY1].spam = 'python'
        t = transaction.get()
        t.note('Transaction 2')
        t.setUser('User 2')
        t.commit()

        annotations[KEY3] = DummyAnnotation()
        t = transaction.get()
        t.note('Transaction 3')
        t.setUser('User 3')
        t.commit()

        del annotations[KEY3]
        annotations[KEY2].spam = 'lumberjack'
        t = transaction.get()
        t.note('Transaction 4')
        t.setUser('User 4')
        t.commit()

        self.object.foo = 'mit'
        annotations[KEY1].spam = 'trout'
        t = transaction.get()
        t.note('Transaction 5')
        t.setUser('User 5')
        t.commit()

    def tearDown(self):
        transaction.abort()
        del self.app
        self._connection.close()
        del self._connection
        self._storage.close()
        del self._storage
        shutil.rmtree(self._dir)

    def test_historyMetadata(self):
        """Each revision entry has unique metadata"""
        for i, entry in enumerate(self.object.getHistories()):
            # History is returned in reverse order, so Transaction 5 is first
            self.assertEqual(entry[2], 'Transaction %d' % (5 - i))
            self.assertEqual(entry[3], '/ User %d' % (5 - i))

    def test_objectContext(self):
        """Objects are returned with an acquisition context"""
        for entry in self.object.getHistories():
            self.assertEqual(entry[0].aq_parent, self.app)

    def test_simpleAttributes(self):
        """Simple, non-persistent attributes are tracked"""
        foo_history = (e[0].foo for e in self.object.getHistories())
        expected = ('mit', 'baz', 'baz', 'baz', 'bar')
        self.assertEqual(tuple(foo_history), expected)

    def test_annotation(self):
        """Persistent subkeys of the __annotations__ object"""
        key1_history = (e[0].__annotations__[KEY1].spam
                        for e in self.object.getHistories())
        expected = ('trout', 'python', 'python', 'python', 'eggs')
        self.assertEqual(tuple(key1_history), expected)

        key2_history = (e[0].__annotations__[KEY2].spam
                        for e in self.object.getHistories())
        expected = ('lumberjack', 'lumberjack', 'eggs', 'eggs', 'eggs')
        self.assertEqual(tuple(key2_history), expected)

    def test_annotationlifetime(self):
        """Addition and deletion of subkeys is tracked"""
        key3_history = (bool(e[0].__annotations__.has_key(KEY3))
                        for e in self.object.getHistories())
        expected = (False, False, True, False, False)
        self.assertEqual(tuple(key3_history), expected)

    def test_maxReturned(self):
        history = list(self.object.getHistories(max=2))
        self.assertEqual(len(history), 2)

def test_suite():
    suite = unittest.TestSuite()
    suite.addTests((
        unittest.makeSuite(ATHistoryAwareTests),
    ))
    return suite

if __name__ == '__main__':
    unittest.main()
