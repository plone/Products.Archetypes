try:
    # Zope >= 2.6
    from Interface import Interface, Attribute
except ImportError:
    # Zope < 2.6
    try:
        from Interface import Base as Interface, Attribute
    except ImportError:
        class Interface:
            """ """
            pass

        class Attribute:
            """ """
            def __init__(self, doc):
                self.doc = doc
