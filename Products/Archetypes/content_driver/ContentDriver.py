class ContentDriver:
    ## The output mimetype
    ## we can adapt from multiple input spec from a
    ## descriptor later
    mime_type = None



    def initialize(self, content_type=None):
        """Return boolean indidating if the converter should be in a
        functional state.

        The content type argument optionally allows the plugin to
        register itself for more than one contenttype doing specific
        work for a given type
        """
        return 1


    def convertData(self, instance, data):
        """takes a BaseUnit instance (that it will populate) and the data to
        operate on. When it extracts image content it will need to write
        URL so that they appear as BC/BU/Image where BC is the BaseContent
        derived type and BU is the BaseUnit for the field with complex data.
        """
        pass
