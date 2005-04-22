from Products import generator as PRODUCT

version=PRODUCT.__version__
modname=PRODUCT.__name__

# (major, minor, patchlevel, release info) where release info is:
# -99 for alpha, -49 for beta, -19 for rc and 0 for final
# increment the release info number by one e.g. -98 for alpha2

major, minor, bugfix =  version.split('.')[:3]
bugfix, release = bugfix.split('-')[:2]

relinfo=-99 #alpha
if 'beta' in release:
    relinfo=-49
if 'rc' in release:
    relinfo=-19
if 'final' in release:
    relinfo=0

numversion = (int(major), int(minor), int(bugfix), relinfo)

at_versions = (
    '1.3.0-final',
    '1.3.1-rc1',
    '1.3.1-rc2',
    '1.3.1-rc3',
    '1.3.1-rc4',
    '1.3.1-final',
    '1.3.2-rc1',
    '1.3.2-final',
    '1.3.3-rc1',
    '1.3.3-rc2',
    '1.3.3-rc3',
    '1.3.3-final',
    ###MARKERFORATRELEASESCRIPT###
    )
license = 'GPL'
copyright = '''Benjamin Saller (c) 2003'''

author = "Archetypes developement team"
author_email = "archetypes-devel@lists.sourceforge.net"

short_desc = "Widget generator for Archetypes"
long_desc = short_desc

web = "http://www.sourceforge.net/projects/archetypes"
ftp = ""
mailing_list = "archetypes-devel@lists.sourceforge.net"

debian_maintainer = "Sylvain Thenault"
debian_maintainer_email = "sylvain.thenault@logilab.fr"
debian_handler = "python-library"
