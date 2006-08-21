# -*- coding: UTF-8 -*-

from Products.azax import AzaxBaseView, force_unicode

class ValidationView(AzaxBaseView):

    # --
    # Kss methods
    # --

    def kssValidateField(self, fieldname, value):
        '''Validate a given field
        '''
        # validate the field, actually
        ##value = force_unicode(value, 'utf')
        instance = self.context.aq_inner
        field = instance.getField(fieldname)
        error = field.validate(value, instance, {})
        # replace the error on the page
        self.issueFieldError(fieldname, error)
        return self.render()

    # XXX full form validation
    def XXX_vali(self, v={}):
        context = self.context
        # Merge the form var is the Request
        context.REQUEST.form.update(v)
        errors = {}
        # Check for Errors
        errors = context.validate(REQUEST=context.REQUEST, errors=errors, data=1, metadata=0)
        if errors:
            pms = 'Please correct the indicated errors.'
            self.replaceInnerHTML(self.getCssSelector('div.portalMessage'),unicode(pms)) 
            ## Display ATFieldErrors
        return self.render()

    # --
    # Helpers
    # --

    def issueFieldError(self, fieldname, error):
        'Issue this error message for the field'
        # XXX translation?
        selector = self.getCssSelector('div#archetypes-fieldname-%s div.fieldErrorBox' % fieldname)
        if error:
            # Blame AT for not using unicodes.
            #error = force_unicode(error, 'utf')
            self.replaceInnerHTML(selector, error)
            klass = 'field error Archetypes%sfield' % fieldname
        else:
            self.clearChildNodes(selector)
            klass = 'field Archetypes%sfield' % fieldname
        # set the field style in the required way
        self.setAttribute(
            self.getHtmlIdSelector('archetypes-fieldname-%s' % fieldname),
            'class', klass)
