from setuptools import setup, find_packages

import sys


if sys.version_info[0] != 2:
    # Prevent creating or installing a distribution with Python 3.
    raise ValueError("Archetypes is Python 2 only.")

version = '1.16.6'

setup(name='Products.Archetypes',
      version=version,
      description="Archetypes is a developers framework for rapidly "
                  "developing and deploying rich, full featured content "
                  "types within the context of Zope/CMF and Plone.",
      long_description=open("README.rst").read() + "\n" +
                       open("CHANGES.rst").read(),
      classifiers=[
        "Development Status :: 6 - Mature",
        "Framework :: Plone",
        "Framework :: Plone :: 5.2",
        "Framework :: Zope2",
        "Framework :: Zope :: 4",
        "License :: OSI Approved :: GNU General Public License (GPL)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 2 :: Only",
        ],
      keywords='Archetypes Plone CMF Zope',
      author='Archetypes development team',
      author_email='plone-developers@lists.sourceforge.net',
      url='https://pypi.org/project/Products.Archetypes',
      license='GPL',
      packages=find_packages(),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      python_requires="==2.7.*",
      extras_require=dict(
        test=[
            'zope.annotation',
            'zope.publisher',
            'zope.testing',
            'plone.app.testing',
            'Products.ATContentTypes',
            'mock',
            'plone.app.robotframework',
        ]
      ),
      install_requires=[
          'setuptools',
          'zope.component',
          'zope.contenttype',
          'zope.datetime',
          'zope.deferredimport',
          'zope.event',
          'zope.i18n',
          'zope.i18nmessageid',
          'zope.interface',
          'zope.lifecycleevent',
          'zope.publisher',
          'zope.schema',
          'zope.tal',
          'zope.viewlet',
          'Products.CMFCore',
          'Products.CMFFormController',
          'Products.DCWorkflow',
          'Products.GenericSetup>=1.8.3',
          'Products.MimetypesRegistry>=2.0.3',
          'Products.PortalTransforms',
          'Products.ZSQLMethods',
          'Products.statusmessages',
          'Products.validation',
          'plone.folder',
          'plone.uuid',
          'plone.app.folder',
          'Acquisition',
          'DateTime',
          'ExtensionClass',
          'transaction',
          'ZODB3',
          'Zope >= 4.0b7.dev0',
          'Zope2',
          'plone.app.widgets>=2.0.0.dev0'
      ],
      )
