from setuptools import setup, find_packages

version = '1.6'

setup(name='Products.Archetypes',
      version=version,
      description="The Plone Content Management System",
      long_description=open("README.txt").read(),
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        ],
      keywords='Archetypes Plone CMF python Zope',
      author='Benjamin Saller and others',
      author_email='plone-developers@lists.sourceforge.net',
      url='http://plone.org/',
      license='BSD',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['Products'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
      ],
      )
