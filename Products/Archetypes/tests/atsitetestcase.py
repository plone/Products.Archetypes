from Testing.ZopeTestCase import Functional
from Products.Archetypes.tests import attestcase
from Products.PloneTestCase.setup import portal_name
from Products.PloneTestCase.setup import portal_owner
import sys, code

from Products.PloneTestCase import PloneTestCase

class ATSiteTestCase(PloneTestCase.PloneTestCase, attestcase.ATTestCase):
    """AT test case with Plone site
    """


class ATFunctionalSiteTestCase(Functional, ATSiteTestCase):
    """AT test case for functional tests with Plone site
    """
    
    def interact(self, locals=None):
        """Provides an interactive shell aka console inside your testcase.
        
        It looks exact like in a doctestcase and you can copy and paste
        code from the shell into your doctest. The locals in the testcase are 
        available, becasue you are in the testcase.
    
        In your testcase or doctest you can invoke the shell at any point by
        calling::
            
            >>> interact( locals() )        
            
        locals -- passed to InteractiveInterpreter.__init__()
        """
        savestdout = sys.stdout
        sys.stdout = sys.stderr
        sys.stderr.write('\n'+'='*70)
        console = code.InteractiveConsole(locals)
        console.interact("""
DocTest Interactive Console - (c) BlueDynamics Alliance, Austria, 2006
Note: You have the same locals available as in your test-case. 
Ctrl-D ends session and continues testing.
""")
        sys.stdout.write('\nend of DocTest Interactive Console session\n')
        sys.stdout.write('='*70+'\n')
        sys.stdout = savestdout


__all__ = ('ATSiteTestCase', 'ATFunctionalSiteTestCase', 'portal_name',
           'portal_owner')
