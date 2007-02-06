
from Products.Five.browser import BrowserView

class DefaultFieldDecoratorView(BrowserView):
    '''Gives a possibility to kss to implement this view,
    meanwhile, allow it to be used from the templates if
    kss is not loaded.
    '''

    def kss_class(self, fieldname, mode, singleclick=False):
        return ''
