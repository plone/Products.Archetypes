==============================
Schema Provider Design
==============================

:Author: Benjamin Saller
:Contact: bcsaller@objectrealms.net
:Date: $Date: 2004/04/14 20:37:55 $
:Version: $Revision: 1.1.2.2 $
:Web site: http://sourceforge.net/projects/archetypes

This is the design for the schema provider model, an abstraction to allow
for advanced schema composition and policy to handle this, all in support
of things like global TTW abilities.

Main Design
==================

Objects and Interfaces
-------------------------	

Schema Manager: 
    The archetypes tool will provide an API for getting additional
    schema elements for composition purposes. Given an object we can
    request any additional schema elements by type or UUID.

Schema Providers:
    An Interface for objects that can provide schema to other
    objects. This means they respond to the collector API somehow.

Schema Collector: 
    A strategy object that can be used to collect the schema that
    apply to an object. This can be based on things like acquisition
    chains or references. In practice the collector strategy should be
    quite simple, but to facilitate a collection of policies we use a
    chaining model where we ask each element returned by a collector
    if it provides additional element by its policy.




Use Cases
==============================

UC1 We have a type of Object with a certain data format we which to represent with Archetypes (traditional case)

UC2 We have a traditional Archetype we wish to augment with some TTW schema modifications

UC3 We have a traditional Archetype and we wish to modify the schema of a particular instance TTW

UC4 We have a traditional Archetype and we wish to composite its schema with another schema provided by another object (containment, reference, etc)

UC5 We have UC4 situation and then wish to modify an instance of such a compositing  TTW

UC6 An object w/o a schema can have one provided to it as an
annotation on it through an adapter or interceptor

Use Case Comments
------------------------------

Obviously we must support UC1. UC2 and UC4 are the same base problem,
we want to composite and modify the class. UC3 and UC5 are harder
given the current impl and the limitations of persistence in Zope2
because we can not modify the instances in a persistent way (this is
not strictly true, we can generate code for modules that we inject
into the base class list and this should work).

To support Instance Based schema in a reliable way I am going to do
away with generated accessors and mutators and provide simple get/set
primitives that take the name of the field they relate to. This will
require modification to the skins and tests but for the most part
should not greatly disturb old code.


Use Case Details
------------------------------

UC2-5: We need policy for merging the various schema. Filesystem code
should generally take priority, but in some cases we need to modify
the presentation attributes of an object while still using FS based
behavior. In other cases we need to remove/disable fields from FS code
or override existing behavior completely. This means that schema must
be merged accoring to policy hints and not a single static method.

To Support Policy merging hooks we need to know certain things about a
schema and where it comes from (does it have FS code), how was it
provided, etc.


