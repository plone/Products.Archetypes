# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and 
#	                       the respective authors. All rights reserved.
# For a list of Archetypes contributors see docs/CREDITS.txt.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
# * Neither the name of the author nor the names of its contributors may be used
#   to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED "AS IS" AND ANY AND ALL EXPRESS OR IMPLIED
# WARRANTIES ARE DISCLAIMED, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF TITLE, MERCHANTABILITY, AGAINST INFRINGEMENT, AND FITNESS
# FOR A PARTICULAR PURPOSE.
#
################################################################################

import os

from AccessControl import ClassSecurityInfo
from Globals import InitializeClass
from OFS.Folder import Folder
from Products.CMFCore.utils import UniqueObject
from Products.PageTemplates.PageTemplateFile import PageTemplateFile

_www = os.path.join(os.path.dirname(__file__), 'www')

class ArchTTWTool(UniqueObject, Folder):
    """ Archetypes TTW Tool """

    id = 'archetypes_ttw_tool'
    meta_type = 'Archetypes TTW Tool'

    security = ClassSecurityInfo()
    meta_types = all_meta_types = (())

    manage_options=(
        (Folder.manage_options[0],) +
        (
        { 'label'  : 'Introspect',
          'action' : 'manage_debugForm',
          },

        )
        + Folder.manage_options[1:]
        )

    fields_template = PageTemplateFile('fields_xml', _www)
    widgets_template = PageTemplateFile('widgets_xml', _www)
    storages_template = PageTemplateFile('storages_xml', _www)
    validators_template = PageTemplateFile('validators_xml', _www)
    types_template = PageTemplateFile('types_xml', _www)
    type_template = PageTemplateFile('type_xml', _www)
    registry_template = PageTemplateFile('registry_xml', _www)

    def fields(self):
        from Registry import availableFields
        fields = [v for k, v in availableFields()]
        return fields

    security.declarePublic('fields_xml')
    def fields_xml(self):
        """ Return XML representation of the field registry """
        fields = self.fields()
        return self.fields_template(fields=fields)

    def widgets(self):
        from Registry import availableWidgets
        widgets = [v for k, v in availableWidgets()]
        return widgets

    security.declarePublic('widgets_xml')
    def widgets_xml(self):
        """ Return XML representation of the widget registry """
        widgets = self.widgets()
        return self.widgets_template(widgets=widgets)

    def storages(self):
        from Registry import availableStorages
        storages = [v for k, v in availableStorages()]
        return storages

    security.declarePublic('storages_xml')
    def storages_xml(self):
        """ Return XML representation of the storage registry """
        storages = self.storages()
        return self.storages_template(storages=storages)

    def validators(self):
        from Registry import availableValidators
        validators = [v for k, v in availableValidators()]
        return validators

    security.declarePublic('validators_xml')
    def validators_xml(self):
        """ Return XML representation of the validators registry """
        validators = self.validators()
        return self.validators_template(validators=validators)

    def types(self):
        from Registry import availableTypes
        types = [v for k, v in availableTypes()]
        return types

    security.declarePublic('types_xml')
    def types_xml(self):
        """ Return XML representation of the types registry """
        types = self.types()
        return self.types_template(types=types)

    security.declarePublic('registry_xml')
    def registry_xml(self):
        """ Return XML representation of the wholeregistry """
        options = {}
        options['fields'] = self.fields()
        options['widgets'] = self.widgets()
        options['storages'] = self.storages()
        options['validators'] = self.validators()
        options['types'] = self.types()
        return self.registry_template(**options)

    security.declarePublic('type_xml')
    def type_xml(self):
        """ Return XML representation of one type from the registry """
        type = self.REQUEST.get('type', '')
        if not type:
            raise ValueError, 'Type is not valid'
        from Products.Archetypes.registries import typeDescriptionRegistry
        type = typeDescriptionRegistry[type]
        return self.type_template(type=type)


InitializeClass(ArchTTWTool)

