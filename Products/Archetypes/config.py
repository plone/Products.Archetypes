PKG_NAME = "Archetypes"
SKIN_NAME = "archetypes"
TOOL_NAME = "archetype_tool" ## Name the tool will be installed under

UID_CATALOG = "uid_catalog"

REGISTER_DEMO_TYPES = True ##Initialize the demo types
DEBUG =  False ## Hide debug messages
#DEBUG = True  ## See debug messages

RENAME_AFTER_CREATION_ATTEMPTS = 100
## Try up to -100 at the end of the id when doing title-to-id renaming


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

## BBB constants for removed graphviz suppport
GRAPHVIZ_BINARY = None
HAS_GRAPHVIZ = False

## protect attributes of AttributeStorage from unallowed access?
ATTRIBUTE_SECURITY = True

## set language default for metadata, it will be overwritten by portal-settings!
LANGUAGE_DEFAULT=u''

## Archetypes before 1.4 managed the catalog map using meta types instead of
## portal types. If you need this old behaviour change this setting to False.
CATALOGMAP_USES_PORTALTYPE = True
