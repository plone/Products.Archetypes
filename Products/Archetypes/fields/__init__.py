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

# import the base fields
from Products.Archetypes.fields.base import Field
from Products.Archetypes.fields.base import ObjectField

# import concrete fields
from Products.Archetypes.fields.text import StringField
from Products.Archetypes.fields.text import TextField
from Products.Archetypes.fields.text import LinesField
from Products.Archetypes.fields.number import IntegerField
from Products.Archetypes.fields.number import FloatField
from Products.Archetypes.fields.number import FixedPointField
from Products.Archetypes.fields.number import BooleanField
from Products.Archetypes.fields.number import DateTimeField
from Products.Archetypes.fields.file import FileField
from Products.Archetypes.fields.file import CMFObjectField
from Products.Archetypes.fields.image import ImageField
from Products.Archetypes.fields.image import PhotoField
from Products.Archetypes.fields.reference import ReferenceField
from Products.Archetypes.fields.computed import ComputedField

# import other classes (for backward compatibility)
from Products.Archetypes.fields.image import ScalableImage, Image
from Products.Archetypes.fields.text import encode, decode

