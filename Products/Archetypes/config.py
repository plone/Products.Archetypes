from Products.PortalTransforms.libtransforms import utils as transform_utils

PKG_NAME = "Archetypes"
SKIN_NAME = "archetypes"
TOOL_NAME = "archetype_tool" ## Name the tool will be installed under

UID_CATALOG = "uid_catalog"

REGISTER_DEMO_TYPES = True ##Initialize the demo types
INSTALL_DEMO_TYPES = False ##Install the demo types
#INSTALL_DEMO_TYPES = True
DEBUG = True  ## See debug messages

##Reference Engine bits
REFERENCE_CATALOG = "reference_catalog"
UUID_ATTR = "_at_uid"
REFERENCE_ANNOTATION = "at_references"

##ordered folder handling
##implement the old style ordered folder?
##for backward compatibility reasons only
USE_OLD_ORDEREDFOLDER_IMPLEMENTATION = False

## In zope 2.6.3+ and 2.7.0b4+ a lines field returns a tuple not a list. Per
## default archetypes returns a tuple, too. If this breaks your software you
## can disable the change.
## See http://zope.org/Collectors/Zope/924
ZOPE_LINES_IS_TUPLE_TYPE = True

## MYSQL SQLStorage Table Type
## To use connections with ACID transactions you should define it as
## INNODB. The MySQL default table type is MyISAM.
MYSQL_SQLSTORAGE_TABLE_TYPE = 'INNODB'

## Debug security settings of Fields, Widgets and Storages?
DEBUG_SECURITY=False
#DEBUG_SECURITY=True

## If you have graphviz http://www.research.att.com/sw/tools/graphviz/
## and its frontend "dot" installed on your system set this to True
## You need dot version > 1.10 with cmapx support.
try:
    GRAPHVIZ_BINARY = transform_utils.bin_search('dot')
except transform_utils.MissingBinary:
    # graphviz not found
    GRAPHVIZ_BINARY = None
    HAS_GRAPHVIZ = False
else:
    HAS_GRAPHVIZ = True

## comment out the following line to enable the reference graph tool
HAS_GRAPHVIZ = False
