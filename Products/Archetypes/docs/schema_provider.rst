==============================
Schema Provider Design
==============================

:Author: Benjamin Saller
:Contact: bcsaller@objectrealms.net
:Date: $Date: 2004/04/20 15:37:16 $
:Version: $Revision: 1.1.2.4 $
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

UC7 We want to define a totally new type TTW. Add a type (select from
existing schema as building blocks (BaseSchema for example)) and then
add in new fields.


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



Implementation Notes
========================================

We need the policy triggers to live global but the implementation to
be controllable from the instance.

class Foo(BaseContent):
        collector = ATToolCollection() #impl that delegates to the
                                       #tool for all its policy (and
                                       #the gloabl default)

class Bar(BaseContent):
        collector = NonCollector() # we only use self.schema and can't
                                   # have other things applied to us


before I confused AXIS with policy where the policy might be to check
1.n axis

what we want is to:
        be able to register new axis
        not have to change instances when we do
        allow user types to have new behavior
        allow user types to pick up existing behavior
        we need to allow for caching and inexpensive (--time) verification


not so bad.

We have CollectorStrategy (CS) objects and CollectorPolicy (CP)
objects. The type or instance is assocaited with a CP. The CP will use
CS to do its work (generally). The CP will have information about the
global module space registry and the portal/tool specific
versions. Using this it can do it work.

The portal tool should reserve a persistent space for each axis to
record information it might need to do it work.


When viewing an object we need to be able to look at its list of
providers, find the sources of its schema and manipulate those. This
is a little harder. Axis may be made available via the CP that the
instance has no direct relationship to. For this we introduce a
SchemaSource (SS) object. The SS object must tell us eveything we need
to know to composite the schemas into a single entity, source, how we
got it, the schema, the source object (if there is one (in context)).

The general flow is as follows:

I  = Instance
AT = Archetype Tool
DP = Default Collection Policy (Using AT)
::

        I               DP              AT      CS      SS
        Schema() ->
        _collect        Collect(I)
                                        Gather [CS]
                                                Gather SS
                [SS] <-         -       -
        _composite ->   Composite(I, SS)



We hand the SS objects back to I.Schema() so that it can be totally
overridden by user code (YAGNI) but is then passed back to the policy
for centralized management.


Foreseen Issues
----------------------------------------
We need for policy to map priority or relevance to fields and schema
on axes that may be registered at runtime. We need a better interface
for this.

We need to scan the full fieldset, making sure to preserve FS based
behavior. (I think.... this is a dusty corner of policy)





Notes
========================================

A cool usecase to support would be a type of schema field setting that
says:
        when set create another field of my type after me in the
schema


so you could have an imageSet and adding a new one would create a new
box on the form. the UI would take some work, but the idea is good for
demoing what we can do now.
