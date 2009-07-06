Archetypes Unit Testing Suite

  Requirements
  
    ZopeTestCase
    
      download and install latest from 
      "collective SVN":https://svn.plone.org/svn/collective/ZopeTestCase/trunk/


    CMFTestCase

      download and install latest from 
      "collective SVN":https://svn.plone.org/svn/collective/CMFTestCase/trunk/

      
  How to run the unit tests

    Very simple (unix-like OS only)::

      INSTANCE_HOME/bin/zopectl test Archetypes

    Simple::
  
      export SOFTWARE_HOME=/path/to/Zope/lib/python 
      python runalltests.py

    Using a testrunner, e.g.::

      python /path/to/Zope/bin/testrunner.py -qid .
