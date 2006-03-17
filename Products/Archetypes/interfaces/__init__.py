"""
This file is here to make the module importable.
"""
from _base import *
from _referenceable import IReferenceable

import base
import referenceable

from Interface.bridge import createZope3Bridge
createZope3Bridge(IBaseObject, base, 'IBaseObject')
createZope3Bridge(IBaseContent, base, 'IBaseContent')
createZope3Bridge(IBaseFolder, base, 'IBaseFolder')
createZope3Bridge(IBaseUnit, base, 'IBaseUnit')

createZope3Bridge(IReferenceable, referenceable, 'IReferenceable')
