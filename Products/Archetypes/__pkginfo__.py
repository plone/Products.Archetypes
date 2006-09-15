from Products import Archetypes as PRODUCT
import os.path

version=PRODUCT.__version__
modname=PRODUCT.__name__

# (major, minor, patchlevel, release info) where release info is:
# -99 for alpha, -49 for beta, -19 for rc and 0 for final
# increment the release info number by one e.g. -98 for alpha2

major, minor, bugfix =  version.split('.')[:3]
bugfix, release = bugfix.split('-')[:2]

relinfo = None
if 'alpha' in release:
    relinfo=-99
if 'beta' in release:
    relinfo=-49
if 'rc' in release:
    relinfo=-19
if 'final' in release:
    relinfo=0

if relinfo is None:
    relinfo = -9

numversion = (int(major), int(minor), int(bugfix), relinfo)

license = 'BSD like'
license_text = open(os.path.join(PRODUCT.__path__[0], 'LICENSE.txt')).read()
copyright = '''Copyright (c) 2003-2004 Benjamin Saller <bcsaller@yahoo.com>'''

author = "Archetypes developement team"
author_email = "archetypes-devel@lists.sourceforge.net"

short_desc = "A developers framework for rapidly developing and deploying rich, full featured content types within the context of Zope/CMF and Plone"
long_desc = """Archetypes
     Archetypes is a developers framework for rapidly developing and 
     deploying rich, full featured content types within the context of 
     Zope/CMF and Plone.
.
     Archetypes is based around the idea of an _Active Schema_. Rather
     than provide a simple description of a new data type Archetype
     schemas do the actual work and heavy lifting involved in using
     the new type. Archetype Schemas serve as easy extension points
     for other developers as project specific components can be
     created and bound or you can choose among the rich existing set
     of features.
.
Features
    * Simple schemas with working default policy.
    * Power and flexibility with lowered incidental complexity.
    * Integration with rich content sources such as Office Product Suites.
    * Full automatic form generation
"""

web = "http://plone.org/products/archetypes"
ftp = ""
mailing_list = "archetypes-devel@lists.sourceforge.net"

debian_name = "zope-cmfarchetypes"
debian_maintainer = "Sylvain Thenault"
debian_maintainer_email = "sylvain.thenault@logilab.fr"
debian_handler = "zope"
