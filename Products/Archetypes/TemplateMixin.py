from Products.Archetypes.Schema import Schema
from Products.Archetypes.Field import StringField
from Products.Archetypes.Widget import SelectionWidget
from Products.Archetypes.config import TOOL_NAME

from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.utils import getToolByName

schema = Schema((
    StringField('layout',
                accessor="getLayout",
                mutator="setLayout",
                default="base_view",
                vocabulary="templates",
                widget=SelectionWidget(
                                       visible={'view' : 'invisible'},
                                       )
                ),
        ))


class TemplateMixin:
    schema = schema
    actions = (
        { 'id': 'view',
          'name': 'View',
          'action': 'view',
          'permissions': (CMFCorePermissions.View,),
        }, )

    aliases = {
        '(Default)':'',
        'index_html': '',
        'view':'',
        'gethtml':'source_html'}


    index_html = None
    def __call__(self):
        """return a view based on layout"""
        v = getTemplateFor(self, self.getLayout())
        return v(self, self.REQUEST)

    def templates(self):
        at = getToolByName(self, TOOL_NAME)
        return at.lookupTemplates(self)

def getTemplateFor(self, pt, default="base_view"):
    ## Let the SkinManager handle this
    ## But always try to show something
    pt = getattr(self, pt, getattr(self, default))
    return pt
