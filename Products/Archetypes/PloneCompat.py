"""make some plone utilities available to raw CMF sites
"""

import transaction
import logging
logger = logging.getLogger('Archetypes')

try:
    from Products.CMFPlone.utils import transaction_note
except ImportError:
    def transaction_note(note):
        """ Write human legible note """
        T=transaction.get()
        if (len(T.description)+len(note))>=65533:
            logger.warning('Transaction note too large omitting %s' % str(note))
        else:
            T.note(str(note))
