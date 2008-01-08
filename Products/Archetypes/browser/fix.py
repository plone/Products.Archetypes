from Acquisition import aq_inner
from Products.Five.browser import BrowserView
from Products.Archetypes.BaseObject import BaseObject
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from cStringIO import StringIO


class RemoveSchemaAttributes(BrowserView):

    template = ViewPageTemplateFile("remove-schema-attributes.pt")

    def __call__(self):
        context = aq_inner(self.context)
        if 'at_remove_schema_attributes' in self.request.form:
            text = "Removing schema attribute from these items (if any):\n"
            out = StringIO()

            def func(obj, path):
                if isinstance(obj, BaseObject) and 'schema' in obj.__dict__:
                    print >> out, path
                    delattr(obj, 'schema')

            try:
                result = context.ZopeFindAndApply(context,
                    search_sub=True, apply_func=func)
                text += out.getvalue()
            finally:
                out.close()
            return text
        return self.template()
