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

IMPORTANT: Notes for version 1.3.6 or later

  Archetypes 1.3.6 fixes the important problem of multiple reindexObject calls 
  on object creation and save (thx Sidnei et al).

  Due to a bug in portal_factory which was fixed in Plone 2.1.2-rc1 and later
  Archetypes had a problem with kind of ghost-references in Reference-Catalog 
  right after the fix of Archetypes-bug above. If you upgrade your Archetypes to
  1.3.6 or later be aware to upgrade your Plone 2.0.x to at least 2.0.6 or 
  2.1.x to 2.1.2; or backport portal_factory to the Plone version you use.

Features

  * Simple schemas with working default policy.

  * Power and flexibility with lowered incidental complexity.

  * Integration with rich content sources such as Office Product Suites.

  * Full automatic form generation

  * Unique Ids for objects

  * Object References/Relationships

  * Per Type cataloging in one or more catalogs

Requires

  * CMF 1.4.7+ or CMF 1.5.3

  * Zope 2.7.5+ or Zope 2.8.5+, may work with Zope 2.9

  * CMFFormController 1.0.3-beta+

Recommended

  * Plone 2.0.6+ or Plone 2.1.2+

  Archetypes do not work without the following closely related products. You get 
  them with the Archetypes release bundle tarball. You can also fetch them also
  from the plone.org subversion repository .
  
  * PortalTransforms

  * MimetypesRegistry

  * generator

  * validation

  * docutils > 0.3.3 (shipped with Zope)
  
  * Python Imgaging Library 1.1.5+ (1.1.3+ may work partly)

  **Note:** Installing generator and validation as Python packages is no
  longer supported by Archetypes. If they are installed as Python packages,
  they will be silently ignored.


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

 You can find ZopeTestCase and PloneTestCase at http://svn.plone.org/collective/
 For now you have to get the cvs versions!

Documentation

  Major resource for documentation is located at 
  "plone.org":http://plone.org/products/archetypes/documentation
