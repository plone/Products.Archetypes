try:
    # zope-bound validator
    import Zope
    from ZService import ZService as Service
except ImportError:
    # stand alone validator
    from service import Service

from validators import initialize

validation = Service()

initialize(validation)
