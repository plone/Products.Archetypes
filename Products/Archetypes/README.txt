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
    * i18n content on a field basis

Requires
	Plone 1.0+
	CMF 1.3+
	Zope 2.5.1+ (Recommending 2.6.0+)

        You have to install the "generator" and "validation" python packages 
        available on SF Archetypes CVS.

        WARNING ! Those packages was used to be installed as Zope products, 
        this not the case anymore. They should be installed as regular python 
        package (look at the packages'README file for more info). If you're 
        really allergic to distutils, you can keep them as provided in your 
        Products and that should work anyway.

        Zope product "PortalTransforms" should also be installed if you want 
        to use the new base units. You should also install the
        I18NTExtIndexNG product if you want to use the i18n content
        features of archetypes. All that products are also available
        on SF Archetypes CVS.


Quickstart
    
    1) Use the quickinstaller_tool and install archetypes

    Or, in an existing Plone site,

    1) Edit config.py and change INSTALL_DEMO_TYPES to 1
    2) restart server
    3) Create an external method, module Archetypes.Install, function: install
    4) Run it



Documentation
    See the docs directory.
