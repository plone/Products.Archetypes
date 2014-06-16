from DateTime import DateTime


def updateCreationOnCopy(obj, event):
    """ Update creation date when object duplicated via copy/paste"""
    obj.setCreationDate(DateTime())
    obj.reindexObject(idxs=['created'])
