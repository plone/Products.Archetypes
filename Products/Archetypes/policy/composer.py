from Persistence import Persistent
from Products.Archetypes import public as atapi
import sourceset
from sets import Set

class Composer(Persistent):
    """Compose particular bits of policy into a single object,
    These should follow the rules of a policy but not decide on those
    rules. For example the manager might annotate each object in the
    source set after the collect phase with priority. The composer
    should honor that priority when doing the composition but wouldn't
    for example know how to make the priority determination, only how
    to do the lifting of building the single object.
    """
    __name__ = None

    def interested(self, object):
        return False

    def compose(self, sourceSet):
        """Compose returns the end policy product and the work done
        so the tool can record the proper mapping between the policy
        object(s) and the axis/policyProvider tuple that originated
        the contribution to the final policy. If its None, nothing
        will be recorded but it will make change detection,
        notification and editing nigh impossible."""
        return None, None



class SchemaComposer(Composer):
    def interested(self, object):
        return isinstance(object, atapi.Schema)

    def compose(self, sourceSet):
        """Build a schema from the sourceset"""
        # Build a map of all fields by priority
        # this will drive a merge into a single schema
        fieldPri = {}
        for axis, schemaPri, sourceSchema in sourceSet:
            for f in sourceSchema.fields():
                fieldPri.setdefault(schemaPri, list()).append((axis, f, sourceSchema))

        current_fields = Set()
        schema = atapi.Schema()
        priorityLevels = fieldPri.keys()
        priorityLevels.sort(reverse=True)
        work = {}
        for level in priorityLevels:
            for axis, field, ss in fieldPri[level]:
                if field.getName() not in current_fields:
                        # XXX if it is in found set we should still look
                        # for accessor/mutator names which may bind to
                        # real methods. In general we don't want to give
                        # up behavior and so we will codify this behavior
                        # as the default.
                        schema.addField(field)
                        current_fields.add(field.getName())
                        work[field.uuid] = (axis.uuid, ss.uuid)

        return schema, work



class BehaviorComposer(Composer):
    pass
