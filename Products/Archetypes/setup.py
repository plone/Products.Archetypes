#!/usr/bin/env python

""" Setup script """

from distutils.core import setup, Extension
from distutils import util

from __pkginfo__ import modname, version, license, short_desc, long_desc,\
     web, author, author_email

if __name__ == '__main__' :
    dist = setup(name = modname,
                 version = version,
                 license =license,
                 description = short_desc,
                 long_description = long_desc,
                 author = author,
                 author_email = author_email,
                 url = web,
                 package_dir = {'generator': '.'},
                 packages = ['generator',
                             ],
                 )
