Introduction
============

Archetypes is a developers framework for rapidly developing and deploying
rich, full featured content types within the context of Zope/CMF and Plone.

Archetypes is based around the idea of an `Active Schema`. Rather than
provide a simple description of a new data type, Archetype schemas do the
actual work and heavy lifting involved in using the new type. Archetype
Schemas serve as easy extension points for other developers as project
specific components can be created and bound or you can choose among the
rich existing set of features.

Features
--------

* Simple schemas with working default policy.

* Power and flexibility with lowered incidental complexity.

* Full automatic form generation

* Unique Ids for objects

* Object References/Relationships

* Per Type cataloging in one or more catalogs

Unit testing
------------

* Go into the root of your buildout and run::

    bin/test Products.Archetypes

Documentation
-------------

Major resource for documentation is located at `plone.org`_.

.. _plone.org: http://plone.org/products/archetypes/documentation
