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

"""make some plone utilities available to raw CMF sites
"""

try:
    from Products.CMFPlone.PloneUtilities import IndexIterator
except ImportError:
    class IndexIterator:
        __allow_access_to_unprotected_subobjects__ = 1

        def __init__(self, upper=100000, pos=0):
            self.upper=upper
            self.pos=pos

        def next(self):
            if self.pos <= self.upper:
                self.pos += 1
                return self.pos
            raise KeyError, 'Reached upper bounds'

try:
    from Products.CMFPlone import transaction_note
except ImportError:
    def transaction_note(note):
        """ Write human legible note """
        T=get_transaction()
        if (len(T.description)+len(note))>=65535:
            log('Transaction note too large omitting %s' % str(note))
        else:
            T.note(str(note))

