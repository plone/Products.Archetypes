import os, sys, textwrap

if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from Testing import ZopeTestCase
from AccessControl import Unauthorized

from Products.CMFCore.utils import getToolByName
from Products.Archetypes.tests.atsitetestcase import ATSiteTestCase
from Products.Archetypes.tests.utils import makeContent

from Products.Archetypes.Storage import AttributeStorage
from Products.Archetypes.examples.SimpleType import TestView, TestWrite

class AttributeProtectionTest(ATSiteTestCase):

    _type = 'SimpleProtectedType'

    def afterSetUp(self):
        ATSiteTestCase.afterSetUp(self)
        self.setRoles(['Manager'])
        self.portal.invokeFactory('Folder', 'test_folder_')
        self.folder = self.portal.test_folder_
        t = self._type
        self.inst = inst = makeContent(self.folder, portal_type=t, id=t)
        self.object_id = t
        self.attrs = [f.getName() for f in inst.Schema().fields()
                      if isinstance(f.getStorage(), AttributeStorage)]

        self.check_attrs = """\
        content = getattr(context, '%(object_id)s')
        for attr in %(attrs)s:
            print getattr(content, attr, None)
        """ % {'object_id': self.object_id,
               'attrs': self.attrs}

        self.check_methods = """\
        content = getattr(context, '%(object_id)s')
        for meth in %(methods)s:
            print getattr(content, meth)()
        """ % {'object_id': self.object_id,
               'methods': ['foo']}
        self.logout()

    def addPS(self, id, params='', body=''):
        factory = self.folder.manage_addProduct['PythonScripts']
        factory.manage_addPythonScript(id)
        body = textwrap.dedent(body)
        self.folder[id].ZPythonScript_edit(params, body)

    def check(self, psbody):
        self.addPS('ps', body=psbody)
        try:
            self.folder.ps()
        except (ImportError, Unauthorized), e:
            self.fail(e)

    def checkUnauthorized(self, psbody):
        self.addPS('ps', body=psbody)
        try:
            self.folder.ps()
        except (AttributeError, ImportError, Unauthorized), e:
            pass
        else:
            raise AssertionError, 'Unauthorized not raised'

    def test_attribute_access_has_perm(self):
        self.check(self.check_attrs)

    def test_attribute_access_no_perm(self):
        self.setRoles(['Manager'])
        p = self.inst
        p.manage_permission(TestView, roles=['Manager'], acquire=0)
        self.setRoles([])
        self.checkUnauthorized(self.check_attrs)

    def test_method_access_has_perm(self):
        self.check(self.check_methods)

    def DISABLEDtest_method_access_no_perm(self):
        # XXX Fails in my Zope from Zope-2_7-branch, but works with
        # Zope from trunk.
        self.setRoles(['Manager'])
        p = self.inst
        p.manage_permission(TestView, roles=['Manager'], acquire=0)
        self.setRoles([])
        self.logout()
        self.checkUnauthorized(self.check_methods)

    def test_field_write_no_perm(self):
        # Check that if the user doesn't have the
        # field.write_permission then the value will not be updated in
        # edit() or update().
        self.setRoles(['Manager'])
        p = self.inst
        p.manage_permission(TestWrite, roles=['Manager'], acquire=0)
        self.setRoles([])

        title = p.Title()
        p.update(title='Bla')
        self.failUnlessEqual(title, p.Title())

        title = p.Title()
        p.edit(title='Bla')
        self.failUnlessEqual(title, p.Title())

        title = p.Title()
        p.processForm(data=True, values={'title':'Bla'})
        self.failUnlessEqual(title, p.Title())

    def test_field_write_has_perm(self):
        # Check that if the user does have the field.write_permission
        # then the value will be updated in edit() or update().
        p = self.inst
        p.update(title='Bla1')
        self.failUnlessEqual(p.Title(), 'Bla1')

        title = p.Title()
        p.edit(title='Bla2')
        self.failUnlessEqual(p.Title(), 'Bla2')

        title = p.Title()
        p.processForm(data=True, values={'title':'Bla3'})
        self.failUnlessEqual(p.Title(), 'Bla3')

def test_suite():
    import unittest
    suite = unittest.TestSuite()
    tests = []
    tests.append(AttributeProtectionTest)
    for klass in tests:
        suite.addTest(unittest.makeSuite(klass))
    return suite

if __name__ == '__main__':
    framework(descriptions=0, verbosity=1)
