==============================
Schema Provider Design
==============================

:Author: Benjamin Saller
:Contact: bcsaller@objectrealms.net
:Date: $Date: 2004/03/30 23:38:33 $
:Version: $Revision: 1.1.2.1 $
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




Details
---------------------------

