from Persistence import Persistent
from ZODB.PersistentMapping import PersistentMapping

class PolicyEngine(Persistent):
    """
    The policy engine design and motivation is described in
    docs/policyEngine.txt.

    Documentation here refers to the implmentation.
    """

    def __init__(self):
        # Named providers
        self._axes = PersistentMapping()

        # The scheme we use to collect/compose policy
        self._policyManagers = PersistentMapping()
        self._defaultManager = None

        # A mapping between a uuid and its target object
        self._uuid_policy_map = PersistentMapping()

        # A mapping better policyComposites subobjects
        # and the (axis, sourceObject) that provide them
        self._policyProviderMap = PersistentMapping()

    # Axis Management
    def registerAxis(self, axis):
        self._axes[axis.__name__] = axis

    def getAxes(self):
        return self._axes.values()

    def getAxisById(self, name):
        return self._axes[name]


    # Manager Management
    # usually one management policy is enough
    # but we can support _n_
    def registerManager(self, manager):
        # Add a manager
        self._policyManagers[manager.getId()] = manager

    def unregisterManager(self, manager):
        # Remove a manager by Name
        del self._policyManagers[manager]

    def getPolicyManager(self, managerName):
        return self._policyManagers[managerName]

    def setDefaultPolicyManager(self, name):
        if name in self._policyManagers.keys():
            self._defaultManager = name
        else:
            raise ValueError("Not a registered manager: %s" % name)

    def getDefaultPolicyManager(self):
        if self._defaultManager:
            return self._policyManagers[self._defaultManager]
        return None

    # UUID methods
    def getPolicyByUUID(self, uuid):
        return self._uuid_policy_map[uuid]

    def setPolicyByUUID(self, uuid, policy):
        self._uuid_policy_map[uuid] = policy

    def delPolicyByUUID(self, uuid):
        del self._uuid_policy_map[uuid]


    # Collect/Compose Interface
    def getPolicy(self, instance, policyManager=None, **qualifiers):
        """
        Gather the complete unit of policy for a given operation. This
        will use the policy manager (either obtained by looking at
        the instance and operation, or the passed in name of a
        manager) and collect the complete product for a given
        instance.
        """
        if not policyManager:
            policyManager = self._resolveManager(instance, **qualifiers)

        if not policyManager:
            raise ValueError( \
                "No Policy Manager associated with %s, %s" %
                (instance, operation)
                )

        # This is the minimum amount of work needed to cache
        sourceSet = policyManager.collect(instance,
                                          engine=self, **qualifiers)
        policy, work = policyManager.compose(instance, sourceSet,
                                             engine=self, **qualifiers)

        if work: self.recordWork(work)

        return policy


    def _resolveManager(self, instance, **qualifiers):
        #for manager in self._policyManagers.itervalues():
        #    if manager.active(instance, **qualifiers):
        #        return manager
        return self.getDefaultPolicyManager()

    def recordWork(self, work):
        # work is a mapping between the uuids of the detecable policy
        # entities (for example fields of a composed schema) and
        # tuples of uuids of (axis, policySourceObject) pairs
        # it is used in the editing/mutation case to identify the
        # source of bits of policy and must be recorded on the engine

        ## Why this works is important. Even if 3 axes provide the
        ## same field (for example) under different priority the one
        ## that will be recorded is the one that made it into the
        ## result set.
        self._policyProviderMap.update(work)
