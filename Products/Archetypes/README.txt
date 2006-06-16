Archetypes

  Archetypes is a developers framework for rapidly developing and deploying 
  rich, full featured content types within the context of Zope/CMF and Plone.

  Archetypes is based around the idea of an _Active Schema_. Rather
  than provide a simple description of a new data type, Archetype
  schemas do the actual work and heavy lifting involved in using
  the new type. Archetype Schemas serve as easy extension points
  for other developers as project specific components can be
  created and bound or you can choose among the rich existing set
  of features.

Features

  * Simple schemas with working default policy,

  * Power and flexibility with lowered incidental complexity,

  * Integration with rich content sources such as Office Product Suites,

  * Full automatic form generation,

  * Unique Ids for objects,

  * Object References/Relationships,

  * Per Type cataloging in one or more catalogs,

  * transparent and pluggable transformations from one mime-type to another.

Requires

  * CMF 1.5.5+ or CMF 1.6.0+

  * Zope 2.8.7+, or Zope 2.9.3+

  * CMFFormController 1.0.7+

  * Python Imgaging Library 1.1.5+

  Archetypes do not work without the following closely related products. You get 
  them with the Archetypes release bundle tarball. You can also fetch them also
  from the plone.org subversion repository .
  
  * PortalTransforms

  * MimetypesRegistry

  * validation

Recommended

  * Plone 2.5.0+ (Plone 2.1.3+ with Zope 2.8 should work also)

  Archetypes bundle also contains Marshall, a product for flexible Marshallers.

Quickstart

  1. Use the quickinstaller_tool and install archetypes

  Or, in an existing Plone site:

  1. Edit config.py and change INSTALL_DEMO_TYPES to 1

  2. restart server

  3. Create an external method, module Archetypes.Install, function: install

  4. Run it

Unit testing

 * Install ZopeTestCase into ZOPE_HOME/lib/python/Testing
 
 * Install the PloneTestCase product

 * Go into the root of your instance and run 
   ZOPE_HOME/bin/test.py -v -C etc/zope.conf --libdir Products/Archetypes/

 You can find ZopeTestCase and PloneTestCase at http://svn.plone.org/svn/collective/
 For now you have to get the cvs versions!

Documentation

  Major resource for documentation is located at 
  "plone.org":http://plone.org/products/archetypes/documentation
