################################################################################
#
# Copyright (c) 2005, Rocky Burt <rocky@serverzen.com>, and the respective
# authors. All rights reserved.  For a list of Archetypes contributors see
# docs/CREDITS.txt.
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

"""
"""
__author__ = 'Rocky Burt'

__all__ = ('SkinManager',)

import os.path

import zExceptions

from Products.CMFCore.utils import getToolByName, minimalpath
from Products.Archetypes import types_globals
from Globals import package_home

from Products.CMFCore.DirectoryView import addDirectoryViews
from Products.CMFCore.DirectoryView import registerDirectory
from Products.CMFCore.DirectoryView import manage_listAvailableDirectories

# file entries that should get ignored by default (ie not added to skin paths)
DEFAULT_FILE_OMISSIONS = ('.svn', 'CVS')

class SkinException(Exception):
    pass

class MalformedPathException(SkinException):
    pass


def _getTuple(items):
    tuple_ = None

    if isinstance(items, list):
        tuple_ = tuple(items)
    elif isinstance(items, str):
        tuple_ = [x.strip() for x in items.split(',')]
    elif isintance(items, tuple):
        tuple_ = items
    else:
        raise MalformedPathException("Could not convert ["+str(type(items))
                                     +"] to a tuple", items)

    return tuple_
   

def _getPathList(skinsTool, skinName):
    path = skinsTool.getSkinPath(skinName)
    return [i.strip() for i in path.split(',')]


class SkinManager(object):
    """Functionality for manipulating skins and skin paths mostly consisting
    of working with SkinsTool (portal_skins).  Single constructor expects
    a context/object which is either a portal instance or has portal attributes
    acquired.
    """

    _skinsTool = None

    def __init__(self, context):
        object.__init__(self)
        self._skinsTool = getToolByName(context, "portal_skins")
    
    def getSkinPaths(self, skinName=None):
        """Returns all of the elements of a path for the named skin in the
        form of a tuple.  If no skinName is requested, then all skins are
        returned as a dict keyed by skin name with tuples as values.

        >>> sm = SkinManager(portal)
        >>> len(sm.getSkinPaths()) >= 0
        True
        >>> len(sm.getSkinPaths('Nouvelle')) >= 0
        True
        """
        
        result = None

        skinsTool = self._skinsTool
        if skinName:
            result = tuple(_getPathList(skinsTool, skinName))
        else:
            result = {}
            for skinName in skinsTool.getSkinSelections():
                result[skinName] = tuple(_getPathList(skinsTool, skinName))
                
        return result

    def setSkinPaths(self, paths, skinName=None):
        """Sets the path for the named skin.  The paths type should be one of
        list, tuple, or string.  If the paths type is string, all elements
        should be separated by a comma (ie "abc, def, ghi").


        Set the new paths for all skins to the elements contained within
        testing.
        >>> testing = ['abc', 'def']
        >>> sm = SkinManager(portal)
        >>> originalPaths = sm.getSkinPaths()
        >>> firstSkin = originalPaths.keys()[0]
        >>> sm.setSkinPaths(testing)
        >>> newPaths = sm.getSkinPaths()
        >>> newPaths[firstSkin][0] == testing[0]
        True
        >>> newPaths[firstSkin][1] == testing[1]
        True

        Set the new paths for all skins to the value 'onemore'.
        >>> sm.setSkinPaths('onemore', 'Nouvelle')
        >>> newPaths = sm.getSkinPaths('Nouvelle')
        >>> len(newPaths) == 1 and newPaths[0] == 'onemore'
        True
        """
        
        skinsTool = self._skinsTool

        if skinName:
            skinNames = (skinName,)
        else:
            skinNames = skinsTool.getSkinSelections()
            
        for skinName in skinNames:
            if isinstance(paths, list) or isinstance(paths, tuple):
                skinsTool.addSkinSelection(skinName, ','.join(paths))
            else:
                skinsTool.addSkinSelection(skinName, str(paths))

    def addSkinPaths(self, paths, skinName=None, position=None):
        """Adds the specified paths to the named skin.  The paths type should
        be one of list, tuple, or string.  If the paths type is string,
        all elements should be separated by a comma (ie "abc, def, ghi").  The
        position parameter can be used to specify an ordered position within the
        existing path to add the new path items.  The position parameter can
        be of type int or string.  If the position is of type int, then an index
        position is used, otherwise, the string is used as the key representing
        an existing path element name, in which case the items are inserted
        before the found item.  If no position is specified then the items
        get appended to the end.


        Add all path elements in testing to all skins (will be appended to the
        end).
        >>> sm = SkinManager(portal)
        >>> originalPaths = sm.getSkinPaths()
        >>> firstSkin = originalPaths.keys()[0]
        >>> testing = ['abc', 'def']
        >>> sm.addSkinPaths(testing)
        >>> newPaths = sm.getSkinPaths()
        >>> newPaths[firstSkin][-1] == testing[1]
        True
        >>> newPaths[firstSkin][-2] == testing[0]
        True

        Insert all path elements in testing to all skins at the very beginning
        of their paths.
        >>> testing = ['ghi', 'jkl']
        >>> sm.addSkinPaths(testing, position=0)
        >>> newPaths = sm.getSkinPaths()
        >>> newPaths[firstSkin][0] == testing[0]        
        True
        >>> newPaths[firstSkin][1] == testing[1]
        True

        Insert all path elements in testing at the position starting at 2, which
        would be following the elements inserted from the previous example.
        >>> testing = ['aaaa', 'bbbb']
        >>> sm.addSkinPaths(testing, position=2)
        >>> newPaths = sm.getSkinPaths()
        >>> newPaths[firstSkin][2] == testing[0]
        True
        >>> newPaths[firstSkin][3] == testing[1]
        True
        """
        
        skinsTool = self._skinsTool

        if skinName:
            skinNames = (skinName,)
        else:
            skinNames = skinsTool.getSkinSelections()
            
        pathsToAdd = _getTuple(paths)
        for skinName in skinNames:
            newPaths = _getPathList(skinsTool, skinName)
            pos = None
            if position == None:
                newPaths.extend(pathsToAdd)
            elif isinstance(position, str):
                try:
                    pos = newPaths.index(position)
                except ValueError:
                    pass
            elif isinstance(position, int):
                pos = position

            if pos is not None:
                for x in range(len(pathsToAdd)):
                    newPaths.insert(pos+x, pathsToAdd[x])

            self.setSkinPaths(newPaths, skinName)

    def removeSkinPaths(self, paths, skinName=None):
        """Removes the specified paths from the named skin.  The paths type
        should be one of list, tuple, or string.  If the paths type is string,
        all elements should be separated by a comma (ie "abc, def, ghi").  If
        paths is of type list or tuple then the individual elements can be
        either string's or int's.  If an individual element is an int then
        it represents a path index to be removed.  If the element is a string
        then it represents an item to be searched for and then removed.  If the
        element cannot be found, nothing happens.


        Try removing two items specified by one string and one index
        position.
        >>> sm = SkinManager(portal)
        >>> sm.setSkinPaths(['one', 'two', 'three'], 'Nouvelle')
        >>> sm.removeSkinPaths(['two', 2], 'Nouvelle')
        >>> sm.getSkinPaths('Nouvelle')
        ('one',)
       
        Try removing two elements by specifying one string with the names
        separated by a comma.
        >>> sm.setSkinPaths(['one', 'two', 'three', 'four'], 'Nouvelle')
        >>> sm.removeSkinPaths('three,one', 'Nouvelle')
        >>> sm.getSkinPaths('Nouvelle')
        ('two', 'four')
        
        Try removing two elements by specifying one string with the names
        separated by a comma.  One of the elements will silently be ignored
        because it does not exist.
        >>> sm.setSkinPaths(['one', 'two', 'three', 'four'])
        >>> sm.removeSkinPaths('three,nothere')
        >>> sm.getSkinPaths('Nouvelle')
        ('one', 'two', 'four')
        
        """

        skinsTool = self._skinsTool

        if skinName:
            skinNames = (skinName,)
        else:
            skinNames = skinsTool.getSkinSelections()
            
        pathsToRemove = _getTuple(paths)
        for skinName in skinNames:
            currentPaths = self.getSkinPaths(skinName)
            newPaths = list(currentPaths)
            for x in pathsToRemove:
                if isinstance(x, int):
                    newPaths[x] = None
                elif isinstance(x, str):
                    try:
                        pos = newPaths.index(x)
                        newPaths[pos] = None
                    except ValueError:
                        pass

            done = False
            x = 0
            while x < len(newPaths):
                if newPaths[x] == None:
                    del newPaths[x]
                    x = 0
                else:
                    x = x + 1
                
            self.setSkinPaths(newPaths, skinName)

    def installPathsFromDir(self, dirPath,
                            paths=None, skinName=None, position=None,
                            globals=types_globals,
                            omissions=DEFAULT_FILE_OMISSIONS):
        """Adds all subdirectories found at dirPath as paths.  The paths type
        should be one of list, tuple, or string.  If the paths type is string,
        all elements should be separated by a comma (ie "abc, def, ghi").  The
        position parameter can be used to specify an ordered position within the
        existing path to add the new path items.  The position parameter can
        be of type int or string.  If the position is of type int, then an index
        position is used, otherwise, the string is used as the key representing
        an existing path element name, in which case the items are inserted
        before the found item.  If no position is specified then the items
        get appended to the end.


        Set up a skin path and ensure its set correctly.
        >>> sm = SkinManager(portal)
        >>> sm.setSkinPaths('oneentry')
        >>> sm.getSkinPaths('Nouvelle')
        ('oneentry',)

        Install all paths from a directory and ensure the skin paths got
        updated accordingly.
        >>> sm.installPathsFromDir('tests/input/skins')
        >>> sm.getSkinPaths('Nouvelle')
        ('oneentry', 'skinpath1', 'skinpath2')

        Test to ensure that the directory views got added to the skins tool
        properly.
        >>> from Products.CMFCore.utils import getToolByName
        >>> skinsTool = getToolByName(portal, 'portal_skins')
        >>> ids = skinsTool.objectIds()
        >>> 'skinpath1' in ids and 'skinpath2' in ids
        True
                
        """

        skinsTool = self._skinsTool

        absPath = os.path.join(package_home(globals), dirPath)
        pathList = None
        if paths:
            pathList = _getTuple(paths)
        else:
            pathList = os.listdir(absPath)
            if omissions:
                x = 0
                while x < len(pathList):
                    if pathList[x] in omissions:
                        del pathList[x]
                        x = 0
                    else:
                        x = x + 1

        self.addSkinPaths(pathList, skinName=skinName, position=position)

        relDirPath = minimalpath(absPath)

        registered_directories = manage_listAvailableDirectories()
        if relDirPath not in registered_directories:
            registerDirectory(dirPath, globals)
        
        try:
            addDirectoryViews(skinsTool, dirPath, globals)
        except zExceptions.BadRequest:
            # this will happen often in a reloaded environment, safe to ignore
            pass

