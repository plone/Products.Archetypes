
class SchemaSource(object):
    """
    We expect policy objects to annotate these if needed.
    They are transient.
    """
    def __init__(self, axis, schema):
        self.axis = axis
        self.schema = schema

    def annotate(self, field):
        """Given a field object we want to be able to later identify
        its source. This does that (through delegation to the axis
        manager)
        """
        self.axis.annotate(self, field)


