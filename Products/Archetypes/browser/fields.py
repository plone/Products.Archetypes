from Products.Five.browser import BrowserView


class DefaultFieldDecoratorView(BrowserView):
    '''Gives a possibility to kss to implement this view,
    meanwhile, allow it to be used from the templates if
    kss is not loaded.
    '''

    def getKssUIDClass(self):
        return ''

    def getKssClasses(self, fieldname, templateId=None, macro=None):
        return ''

    def getKssClassesInlineEditable(self, fieldname, templateId, macro=None, target=None):
        return ''
