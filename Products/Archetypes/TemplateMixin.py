from Field import FieldList, ObjectField
from Widget import SelectionWidget
from Products.CMFCore import CMFCorePermissions
from Products.CMFCore.utils import getToolByName
from config import TOOL_NAME

type_mixin = FieldList((
    ObjectField('layout',
                accessor="getLayout",
                mutator="setLayout",
                default="base_view",
                vocabulary="templates",
                widget=SelectionWidget(modes=('edit',),)
                ),
        ))


class TemplateMixin:
    type = type_mixin
    actions = (
        { 'id': 'view',
          'name': 'View',
          'action': 'view',
          'permissions': (CMFCorePermissions.View,),
          },
        )
    
    def __call__(self):
        """return a view based on layout"""
        v = getTemplateFor(self, self.getLayout())
        return v(self, self.REQUEST)

    def templates(self):
        at = getToolByName(self, TOOL_NAME) 
        return at.lookupTemplates(self)

def getTemplateFor(self, pt):
    ## Let the SkinManager handle this
    pt = getattr(self, pt)
    return pt

