#
# Runs all tests in the current directory
#
# Execute like:
#   python runalltests.py
#
# Alternatively use the testrunner:
#   python /path/to/Zope/utilities/testrunner.py -qa
#

import os, sys
if __name__ == '__main__':
    execfile(os.path.join(sys.path[0], 'framework.py'))

from common import TestPreconditionFailed, Xprint

import unittest
TestRunner = unittest.TextTestRunner
suite = unittest.TestSuite()

tests = os.listdir(os.curdir)
tests = [n[:-3] for n in tests if n.startswith('test') and n.endswith('.py')]

for test in tests:
    try:
        m = __import__(test)
        if hasattr(m, 'test_suite'):
            suite.addTest(m.test_suite())
    except TestPreconditionFailed, err:
        Xprint('Can\'t run the unit tests in %s: \n %s' % (test, err))

if __name__ == '__main__':
    TestRunner(verbosity=2).run(suite)
