# -*- coding: UTF-8 -*-
################################################################################
#
# Copyright (c) 2002-2005, Benjamin Saller <bcsaller@ideasuite.com>, and
#                              the respective authors. All rights reserved.
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
from Products.Archetypes.field.base import Field
from Products.Archetypes.field.base import ObjectField

# import concrete fields
from Products.Archetypes.field.text import StringField
from Products.Archetypes.field.text import TextField
from Products.Archetypes.field.text import LinesField
from Products.Archetypes.field.number import IntegerField
from Products.Archetypes.field.number import FloatField
from Products.Archetypes.field.number import FixedPointField
from Products.Archetypes.field.number import BooleanField
from Products.Archetypes.field.number import DateTimeField
from Products.Archetypes.field.file import FileField
from Products.Archetypes.field.file import CMFObjectField
from Products.Archetypes.field.image import ImageField
from Products.Archetypes.field.image import PhotoField
from Products.Archetypes.field.reference import ReferenceField
from Products.Archetypes.field.computed import ComputedField

# import other classes (for backward compatibility)
from Products.Archetypes.field.image import ScalableImage, Image
from Products.Archetypes.field.text import encode, decode
