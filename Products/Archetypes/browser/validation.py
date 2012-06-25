from Acquisition import aq_inner
from Products.Five import BrowserView
from Products.CMFCore.utils import getToolByName
import json

SKIP_VALIDATION_FIELDTYPES = ('image', 'file')


class InlineValidationView(BrowserView):

    def __call__(self, uid, fname, value):
        '''Validate a given field. Return any error messages.
        '''
        res = {'errmsg': ''}

        rc = getToolByName(aq_inner(self.context), 'reference_catalog')
        instance = rc.lookupObject(uid)

        field = instance.getField(fname)
        if field.type not in SKIP_VALIDATION_FIELDTYPES:        
            error = field.validate(value, instance, {})
            if isinstance(error, str):
                error = error.decode('utf', 'replace')
            res['errmsg'] = error or ''

        self.request.response.setHeader('Content-Type', 'application/json')
        return json.dumps(res)
