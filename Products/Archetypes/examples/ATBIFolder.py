from Products.Archetypes.atapi import *
from Products.Archetypes.config import PKG_NAME
from Products.Archetypes.AllowedTypesByIface import AllowedTypesByIfaceMixin

schema = BaseFolderSchema


class ATBIFolder(AllowedTypesByIfaceMixin, BaseFolder):
    """A simple folder that uses AllowedTypesByIfaceMixin"""
    schema = schema

registerType(ATBIFolder, PKG_NAME)
