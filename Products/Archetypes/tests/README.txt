Archetypes Unit Testing Suite

  Requirements
  
    ZopeTestCase
    
      download and install latest from 
      "collective CVS":http://cvs.sourceforge.net/viewcvs.py/collective/ZopeTestCase


    PloneTestCase

      download and install latest from 
      "collective CVS":http://cvs.sourceforge.net/viewcvs.py/collective/PloneTestCase

      
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
