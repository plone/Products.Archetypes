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
