PKG_NAME = "Archetypes"
SKIN_NAME = "archetypes"
TOOL_NAME = "archetype_tool" ## Name the tool will be installed under

UID_CATALOG = "uid_catalog"


REGISTER_DEMO_TYPES = 1 ##Initialize the demo types
INSTALL_DEMO_TYPES = 0 ##Install the demo types
DEBUG = 1  ## See debug messages

#XXX activate experimental baseunit
USE_NEW_BASEUNIT = 1


##Reference Engine bits
REFERENCE_CATALOG = "reference_catalog"
UUID_ATTR = "_at_uid"

##ordered folder handling
##implement the old style ordered folder?
##for backward compatibility reasons only
USE_OLD_ORDEREDFOLDER_IMPLEMENTATION = 0

## In zope 2.6.3+ and 2.7.0b4+ a lines field returns a tuple not a list. Per
## default archetypes returns a tuple, too. If this breaks your software you
## can disable the change.
## See http://zope.org/Collectors/Zope/924
ZOPE_LINES_IS_TUPLE_TYPE = 1