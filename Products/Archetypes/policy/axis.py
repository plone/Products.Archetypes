from Persistence import Persistent
from sourceset import SourceSet


class AxisManager(Persistent):
    """
    Abstract Base for each Axis. Each axis controls the flow of policy
    into (and out of the system) via a single channel.

    The units of policy these managers manipulate are minimally
    standardized in order to support object (de)serilization.

    """
    def getId(self): return self.__name__
    def setId(self, name): self.__name__ = name

    # Policy Change Case
    def updatePolicy(self, event):
        ## The event handler triggered when an object managed by this
        ## axis has changed
        policy = event.sourceObject
        if self.objectManagedByAxis(policy):
            # This should be an invarient or the subscription is wrong
            self.invalidate(self.providedBy(policy), policy)

    def invalidate(self, iterable, policy=None):
        """Invalidate a sequence of iterable objects that are provided
        policy by this object. Used in the event of a change or policy
        retraction.

        The policy argument is included in the event should the need
        arise to know which policy element changed.
        """
        for consumer in iterable:
            consumer.invalidatePolicy(PolicyChange(policy=policy))

    # Register and Publish Policy on Axis
    def register(self, policy, **criteria):
        """
        Register a policy object as a policy provider on this
        axis. This can be additionally qualified as applying only
        within the scope of given criteria which is axis specific.

        Specifying a context requires knowledge about the axis. For
        example a Containment provider might provide the policy object
        to child objects a specific object passed in as part of
        context while a Type provider might provide policy to objects
        of a given type.

        """
        pass

    def unregister(self, identifier, **criteria):
        """
        Unregister a policy object as a policy provider. If a
        qualifying criteria was used in registering the policy it
        must also be used to match it for removal.
        """
        pass

    # Event case management
    # see @policyEngine.txt::AM1
    def collect(self, object, **qualifiers):
        """Return all the policy for the object in a collection. The
        result is always a collection as some axes may return more
        than a single policy object. For example, a containment axis
        might return multiple policy items if each of the objects
        ancestors add additional policy. An empty collection means no
        policy.

        Each qualifier is applied to the criteria used to register the
        object. The interpretation is axis dependent.

        Provided policy should be returned as a
        Archetypes.policy.sourceset.SourceSet object.
        If there are multiple matches and interaxis policy is
        important label them as such within their sourceSet.

        """
        return SourceSet()


    def targets(self, policy, **qualifiers):
        """
        Registered objects have a way of finding the instances they
        provide policy to. This method implements the specific axis'
        target object location strategy
        """
        pass

    def __len__(self):
        """Return the count of registered policy object/context
        combinations provided under this axis.
        """
        return 0
