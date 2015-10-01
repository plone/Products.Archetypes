import textwrap
from AccessControl import Unauthorized

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
        self.portal.portal_workflow.setChainForPortalTypes(
            (t,), ('plone_workflow',))
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
        except (AttributeError, ImportError, Unauthorized):
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
        self.assertEqual(title, p.Title())

        title = p.Title()
        p.edit(title='Bla')
        self.assertEqual(title, p.Title())

        title = p.Title()
        p.processForm(data=True, values={'title': 'Bla'})
        self.assertEqual(title, p.Title())

    def test_field_write_has_perm(self):
        # Check that if the user does have the field.write_permission
        # then the value will be updated in edit() or update().
        p = self.inst
        p.update(title='Bla1')
        self.assertEqual(p.Title(), 'Bla1')

        p.edit(title='Bla2')
        self.assertEqual(p.Title(), 'Bla2')

        p.processForm(data=True, values={'title': 'Bla3'})
        self.assertEqual(p.Title(), 'Bla3')

    def test_import_transaction_note(self):
        self.check('from Products.Archetypes.utils import transaction_note')

    def test_use_transaction_note(self):
        self.check('from Products.Archetypes.utils import transaction_note;'
                   'print transaction_note("foo")')

    def test_import_DisplayList(self):
        self.check('from Products.Archetypes import DisplayList')

    def test_use_DisplayList(self):
        self.check('from Products.Archetypes import DisplayList;'
                   'print DisplayList((("foo", "bar"),)).keys()')

    def test_at_post_scripts_unauthorized(self):
        # at_post_create_script and at_post_edit_script should not
        # be accessible to TTW code at all.
        self.setRoles(['Manager'])
        test = """\
        content = getattr(context, '%(object_id)s')
        content.at_post_create_script()
        content.at_post_edit_script()
        """ % {'object_id': self.object_id}
        self.checkUnauthorized(test)
