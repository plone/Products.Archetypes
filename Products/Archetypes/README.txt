Archetypes

  Archetypes (formerly known as CMFTypes) is a developers framework
  for rapidly developing and deploying rich, full featured content
  types within the context of Zope/CMF and Plone.

  Archetypes is based around the idea of an _Active Schema_. Rather
  than provide a simple description of a new data type Archetype
  schemas do the actual work and heavy lifting involved in using
  the new type. Archetype Schemas serve as easy extension points
  for other developers as project specific components can be
  created and bound or you can choose among the rich existing set
  of features.

Features

  * Simple schemas with working default policy.
  * Power and flexibility with lowered incidental complexity.
  * Integration with rich content sources such as Office Product Suites.
  * Full automatic form generation
  * Unique Ids for objects
  * Object References/Relationships
  * Per Type cataloging in one or more catalogs

Requires

  Plone 2.0+
  CMF 1.4+
  Zope 2.6.1+

  CMFFormController (from collective CVS)

  You have to install the "PortalTransforms", "generator" and
  "validation" Products available on SF Archetypes CVS to your Zope Products
  directory. Installing generator and validation as Python package is not longer
  supported by Archetypes. If you have installed them as Python package they are
  silently ignored.

  You should also install the I18NTExtIndexNG product if you
  want to use the i18n content features of archetypes. All that
  products are also available on SF Archetypes CVS.

Quickstart

  1) Use the quickinstaller_tool and install archetypes

  Or, in an existing Plone site,

  1) Edit config.py and change INSTALL_DEMO_TYPES to 1
  2) restart server
  3) Create an external method, module Archetypes.Install, function: install
  4) Run it

Documentation

  See the docs directory.
