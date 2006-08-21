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
    def kssValidateForm(self, data):
        # Put the form vars on the request, as AT cannot work
        # from data
        self.request.form.update(data)
        # Check for Errors
        errors = self.context.aq_inner.validate(self.request, errors={}, data=1, metadata=0)
        if errors:
            # give the portal message
            self.issuePortalMessage('Please correct the indicated errors.')
            # reset all error fields (as we only know the error ones.)
            self.clearChildNodes(self.getCssSelector('div.field div.fieldErrorBox'))
            # Set error fields
            for fieldname, error in errors.iteritems():
                self.issueFieldError(fieldname, error)
        else:
            # I just resubmit the form then
            # XXX of course this should be handled from here, save the
            # content and redirect already to the result page - I guess
            # I just don't want to clean up AT form submit procedures
            self.addCommand('plone-submitCurrentForm', self.getSelector('samenode', ''))
        return self.render()

    # --
    # Helpers
    # --

    def issuePortalMessage(self, error):
        'Issue this portal message'
        # XXX translation?
        self.replaceInnerHTML(self.getHtmlIdSelector('kssPortalMessage'), error) 
        # Now there is always a portal message but it has to be
        # rendered visible or invisible, accordingly
        self.setStyle(self.getHtmlIdSelector('kssPortalMessage'), 
            'display', error and 'block' or 'none') 

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
