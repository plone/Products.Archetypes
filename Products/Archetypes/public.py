from AccessControl import ClassSecurityInfo
from ArchetypeTool import registerType, process_types, listTypes

from BaseContent import BaseContent
from BaseFolder import BaseFolder
from ExtensibleMetadata import ExtensibleMetadata

from Schema import Schema, MetadataSchema
from Field  import *
from Widget import *

BaseFolderSchema = BaseFolder.type + ExtensibleMetadata.type

BaseSchema = BaseContent.type + ExtensibleMetadata.type
