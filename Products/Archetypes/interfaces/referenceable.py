from interface import Interface, Attribute

class IReferenceable(Interface):

    def getRefs():
        """get all the referenced objects for this object"""

    def getBRefs():
        """get all the back referenced objects for this object"""

    def _register(archetype_tool=None):
        """register with the archetype tool for a unique id"""

    def _unregister():
        """unregister with the archetype tool, remove all references"""

    def UID():
        """ Unique ID """

    def _getUID():
        """ Get current UID """

    def _setUID(id):
        """ Change UID """

    def pasteReference(REQUEST=None):
        """ Use the copy support buffer to paste object references into this object.
        I think I am being tricky. """

    def _notifyOfCopyTo(container, op=0):
        """keep reference info internally when op == 1 (move)
        because in those cases we need to keep refs"""


    def _verifyPasteRef(object):
        """ Verify whether the current user is allowed to paste the
        passed object into self. This is determined by checking to see
        if the user could create a new object of the same meta_type of
        the object passed in and checking that the user actually is
        allowed to access the passed in object in its existing
        context.

        Passing a false value for the validate_src argument
        will skip checking the passed in object in its existing
        context. This is mainly useful for situations where the passed
        in object has no existing context, such as checking an object
        during an import (the object will not yet have been connected
        to the acquisition heirarchy). """

    def _verifyObjectPaste(object, validate_src=1):
        """ """
