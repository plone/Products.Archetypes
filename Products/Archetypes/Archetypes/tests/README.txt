Archetypes Unit Testing Suite

  Requirements
  
    ZopeTestCase
    
      "ZopeTestCase":http://zope.org/Members/shh/ZopeTestCase 0.9.0 or higher. 
      "Download":http://zope.org/Members/shh/ZopeTestCase-0.9.0.tar.gz
      
    ArchetypesTestUpdateSchema 
    
      "Archetypes CVS":http://cvs.sourceforge.net/viewcvs.py/archetypes/ArchetypesTestUpdateSchema
      This package is required for some tests.
      
  How to run the unit tests

    Simple::
  
      export SOFTWARE_HOME=/path/to/Zope/lib/python 
      python runalltests.py

    Using a testrunner, e.g.::

      python /path/to/Zope/bin/testrunner.py -qid .
    
    See CMFPlone/tests/README.txt for more information.
