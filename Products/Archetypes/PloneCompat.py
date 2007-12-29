"""make some plone utilities available to raw CMF sites
"""

import transaction
import logging
logger = logging.getLogger('Archetypes')

try:
    from Products.CMFPlone.utils import IndexIterator
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
    from Products.CMFPlone.utils import transaction_note
except ImportError:
    def transaction_note(note):
        """ Write human legible note """
        T=transaction.get()
        if (len(T.description)+len(note))>=65535:
            logger.warning('Transaction note too large omitting %s' % str(note))
        else:
            T.note(str(note))
