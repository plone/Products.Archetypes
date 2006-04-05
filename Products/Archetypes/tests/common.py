#
# ArchetypesTestCase and ArcheSiteTestCase classes
#

# $Id$

from Testing import ZopeTestCase

class TestPreconditionFailed(Exception):
    """ Some modules are missing or other preconditions have failed """
    def __init__(self, test, precondition):
        self.test = test
        self.precondition = precondition

    def __str__(self):
        return ("Some modules are missing or other preconditions "
                "for the test %s have failed: '%s' "
                % (self.test, self.precondition))

def gen_class(klass, schema=None):
    """generats and registers the klass
    """
    if schema is not None:
        klass.schema = schema.copy()
    registerType(klass, 'Archetypes')
    content_types, constructors, ftis = process_types(listTypes(), PKG_NAME)

def mkDummyInContext(klass, oid, context, schema=None):
    gen_class(klass, schema)
    dummy = klass(oid=oid).__of__(context)
    setattr(context, oid, dummy)
    dummy.initializeArchetype()
    return dummy

