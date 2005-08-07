"""
This module is for calculation the size for stored data
and store it with annotation storage if the size is needed return 
the cached this
"""

from Products.Archetypes.interfaces.base import IBaseUnit
from Products.Archetypes.annotations import getAnnotation
from types import StringTypes,\
                  BooleanType,\
                  FloatType,\
                  IntType,\
                  NoneType,\
                  TupleType,\
                  ListType,\
                  LongType,\
                  StringType

#if someone a customized content_class 
#he has to change file and image import class

from OFS.Image import File as BaseFile
from OFS.Image import Image as BaseImage

class PlugableSizeStorage:
    
    def get_size(self,name, instance, **kwargs):
        """Get the size from annotations storage"""
        aw=getAnnotation(instance)
        return aw.get(name,0)
    
    def set_size(self,name, instance, **kwargs):
        """get the size from data an cache it with annotations"""
        if not getattr(instance.getField(name),'size_significant',False):
            return False
        size = 0
        aw = getAnnotation(instance)
        #my mind is split at this point.
        #the performance will be better here if
        #value would be given as argument and than calculated
        #but if the data is transformed in any way before it is really saved
        #we will calculate the wrong size... hoka
        data = self.get(name, instance, **kwargs)
        if type(data) in StringTypes:
            size = len(data)
        elif isinstance(data, BaseImage) or isinstance(data, BaseFile):
            size = data.get_size()
        elif IBaseUnit.isImplementedBy(data):
            size = data.get_size()
        elif type(data) in (ListType,TupleType):
            size = len(''.join(data))
        elif type(data) in (BooleanType,FloatType,IntType,NoneType,LongType):
            size = 0
        else:
            size = len(str(data))
        
        aw.set(name,size)
