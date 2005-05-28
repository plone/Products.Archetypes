from Products.CMFPlone.Portal import addPolicy
from Products.CMFPlone.CustomizationPolicy import DefaultCustomizationPolicy
from Products.Archetypes.Extensions.Install import install as installArchetypes

class ArchetypeCustomizationPolicy(DefaultCustomizationPolicy):
    """ Install Plone with the Archetypes Package """

    def customize(self, portal):
        # do the base Default install, that gets
        # most of it right
        DefaultCustomizationPolicy.customize(self, portal)

        outStr = doCustomization(portal)
        return outStr.getvalue()

def doCustomization(self):
    from StringIO import StringIO
    out = StringIO()

    # Always include demo types
    result = installArchetypes(self, include_demo=1)
    print >> out, result

    return out.getvalue()

def register(context, app_state):
    addPolicy('Archetypes Site', ArchetypeCustomizationPolicy())
