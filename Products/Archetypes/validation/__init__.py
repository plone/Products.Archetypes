from config import validation
from chain import ValidationChain, V_REQUIRED, V_SUFFICIENT
from exceptions import UnknowValidatorError, FalseValidatorError, AlreadyRegisteredValidatorError
import os.path
__version__ = open(os.path.join(__path__[0], 'version.txt')).read().strip()
