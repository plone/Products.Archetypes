from Products.PortalTransforms.libtransforms import utils as transform_utils

PKG_NAME = "Archetypes"
SKIN_NAME = "archetypes"
TOOL_NAME = "archetype_tool" ## Name the tool will be installed under

UID_CATALOG = "uid_catalog"

REGISTER_DEMO_TYPES = True ##Initialize the demo types
INSTALL_DEMO_TYPES = False ##Install the demo types
DEBUG =  False ## Hide debug messages
#DEBUG = True  ## See debug messages

##Reference Engine bits
REFERENCE_CATALOG = "reference_catalog"
UUID_ATTR = "_at_uid"
REFERENCE_ANNOTATION = "at_references"

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

## protect attributes of AttributeStorage from unallowed access?
ATTRIBUTE_SECURITY = False

## set language default for metadata, it will be overwritten by portal-settings!
## This is in Archetypes 1.3.2 fixated to 'en'. LinguaPlone and i18nLayer don't
## like default here. They expect None. If your product relies on the old
## behaviour and you dont need content-i18n it's save to use 'en'.Otherwise keep
## it None for future. In future versions this will be None!
LANGUAGE_DEFAULT=None
#LANGUAGE_DEFAULT='en'
