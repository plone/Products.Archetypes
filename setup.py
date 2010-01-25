from setuptools import setup, find_packages

version = '1.5.16'

setup(name='Products.Archetypes',
      version=version,
      description="Archetypes is a developers framework for rapidly "
                  "developing and deploying rich, full featured content "
                  "types within the context of Zope/CMF and Plone.",
      long_description=open("README.txt").read(),
      classifiers=[
        "Framework :: Plone",
        "Framework :: Zope2",
        "Programming Language :: Python",
        ],
      keywords='Archetypes Plone CMF Zope',
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
          'Products.Marshall',
          'Products.MimetypesRegistry',
          'Products.PortalTransforms',
          'Products.validation>=1.6.4',
      ],
      )
