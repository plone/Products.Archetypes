Archetypes
     Formerly known as CMFTypes, Archetypes is a developers framework
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

Requires
	Plone 1.0+
	CMF 1.3+
	Zope 2.5.1+ (Recommending 2.6.0+)

        Zope products "generator", "transform", "validation" (also available on SF Archetypes CVS)
        should also be installed.


Quickstart

    Or, in an existing Plone site, 
    
    1) Edit config.py and change INCLUDE_DEMO_TYPES to 1
    2) restart server
    3) Create an external method, module Archetypes.Install, function: install
    4) Run it

    Or,

    Create a new Plone site with ZMI and use the Archetype site customization
       policy in the Add Plone Site page.


Documentation
    See the docs directory.
