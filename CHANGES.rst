Changelog
=========

1.14.1 (2017-06-16)
-------------------

Bug fixes:

- Fix related items widget tests to reflect latest plone.app.widgets changes.
  Refs: https://github.com/plone/plone.app.widgets/pull/159
  [thet]

- Fix bugs with Widget's postback attribute, that prevented fields from
  being populated with the submitted empty value in the case of an error.
  [pgrunewald]


1.14.0 (2017-04-01)
-------------------

Breaking changes:

- Update code to the new indexing operations queueing.
  Part of PLIP 1343: https://github.com/plone/Products.CMFPlone/issues/1343
  [gforcada]


1.13.0 (2017-02-12)
-------------------

New features:

- manage_reindexIndex requires index names (Zope4).
  [tschorr]

- Remove Products.PlacelessTranslationService as dependency b/c it is not used in Archetypes.
  [jensens]

Bug fixes:

- Fix tests to work with HTTP1.0 as well as HTTP1.1 answers.
  [gogobd]

- Fix tests to work with latest plone.app.widgets 2.1.
  [thet]

- Default display value of a ``Vocabulary`` i18n-message must be unicode, enforce.
  Needed to work with latest zope.i18nmessageid 4.0.3 release (and later).
  [jensens]

- fix randomly failing test in ``test_referenceable``.
  [jensens]

- Don't instantiate browser view to check for existence.
  [malthe]

1.12 (2016-12-06)
-----------------

New features:

- Moved selection widget translation tests from CMFPlone to Archetypes.
  [maurits]

- ``OFS.HistoryAware`` was dropped in Zope 4.
  Make AnnotationStorage awareness of it optional.
  [jensens]

- Moved scripts that are only used by Archetypes from CMFPlone
  to Products.Archetypes:
  - ``date_components_support.py``
  - ``show_id.py``
  [jensens, davisagli]

Bug fixes:

- More flexible test of getBestIcon.
  [jensens]


1.11.3 (2016-10-03)
-------------------

Bug fixes:

- Don't use document/folder_icon.gif in the test profile.  Use png instead.  [maurits]

- no allowable_content_types for description (avoid validation)
  [tschorr]


1.11.2 (2016-09-14)
-------------------

Bug fixes:

- Enable unload protection by using pattern class ``pat-formunloadalert`` instead ``enableUnloadProtection``.
  [thet]


1.11.1 (2016-08-18)
-------------------

Bug fixes:

- DateWidget, DatetimeWidget now able to clear previous values.
  [seanupton]

- Use zope.interface decorator.
  [gforcada]


1.11.0 (2016-05-15)
-------------------

New:

- Added uninstall profile.  Most importantly this removes the
  ``archetype_tool``, ``reference_catalog``, and ``uid_catalog``.
  Needs Products.GenericSetup 1.8.3.
  [maurits]

- Removed ``error_log`` from ``toolset.xml``, because this is already
  in the toolset of ``Products.CMFPlone``.   [maurits]

Fixes:

- No longer try to mock plone.app.widgets in tests.  [maurits]
- Removed docstrings from some methods to avoid publishing them.  From
  Products.PloneHotfix20160419.  [maurits]


1.10.13 (2016-02-25)
--------------------

Fixes:

- Replace deprecated ``zope.site.hooks`` import with ``zope.component.hooks``.
  [thet]

- Fix tinymce pattern-options merging to be compatible with change in
  p.a.widgets and p.a.z3cform.
  [alecm]



1.10.12 (2016-02-15)
--------------------

Fixes:

- Replace zope.tal.ndiff with difflib.ndiff. It was removed in zope.tal 4.0.0.
  [pbauer]


1.10.11 (2015-10-27)
--------------------

Fixes:

- White space only pep8 cleanup.  Not in the skins.
  [maurits]

- Removed code for unused types_link_to_folder_contents and
  use_folder_tabs.
  [maurits]


1.10.10 (2015-09-20)
--------------------

- Pull types_link_to_folder_contents values from the configuration registry.
  [esteele]

- Set calendar_starting_year and calendar_future_years_available in registry.
  See https://github.com/plone/Products.CMFPlone/issues/872
  [pbauer]


1.10.9 (2015-09-08)
-------------------

- Defend `defaultRights` method against broken portal_metadata.
  Its schemas are instances of CMFDefault classes, which normally are
  no longer available in Plone 5.  The relevant code has been
  duplicated in ATContentTypes.
  [maurits]

- Compare picklist entry value, not text.
  [paulrentschler]


1.10.8 (2015-07-18)
-------------------

- Moved createObject from ATContentTypes.
  [tomgross]


1.10.7 (2015-05-13)
-------------------

- Remove dependency on CMFDefault
  [tomgross]

- We only support `utf-8` at the moment.
  [tomgross]


1.10.6 (2015-03-26)
-------------------

- Merge PLIP 13091.
  [bloodbare]

- Replace deprecated JavaScript functions with their jQuery equivalents.
  [thet]


1.10.5 (2015-03-13)
-------------------

- Move tests to plone.app.testing.
  [tomgross, timo]

- Integrate plone.app.widgets.
  [vangheem]

- Fix ``MimeTypesRegistry`` test import.
  [thet]

- For Plone 5, support getting markup control panel settings from the
  registry, while still supporting normal portal_properties access for Plone
  < 5.
  [thet]


1.10.2 (2014-10-23)
-------------------

- Correctly determine default value for boolean widget. fixes
  https://dev.plone.org/ticket/9675.
  [dibell]

- make textCounter work in Plone 4.3 because 'jquery-integration.js' was
  disabled and remove jq calls. see
  https://github.com/plone/Products.Archetypes/pull/41
  [sverbois]

- removed encoding from javascript tag to make w3c validator happy, see
  https://github.com/plone/Products.Archetypes/pull/23
  [felipeduardo]

- utils.py
  set default encoding to utf-8 for unicode string in the transaction note.
  [jakke]

- Ported tests to plone.app.testing
  [tomgross]

- Frosted cleanups and some obsolete code removal (ApeSupport)
  [tomgross]

1.10.1 (2014-04-13)
-------------------

- waking instances is cheaper than processing a potentially huge vocabulary
  for getting the title, therefore we handle reference fields seperately
  [zwork, agitator]

- Remove DL's from portal message templates.
  https://github.com/plone/Products.CMFPlone/issues/153
  [khink]


1.10.0 (2014-03-01)
-------------------

- Set logging level to DEBUG for warnings regarding new fields initialized on
  an existing object. INFO level can seriously spam the logs of a busy portal.
  [olimpiurob]

- Ported fix for #13833 from the 1.9.x branch for reindexObjectSecurity
  triggering an error when attempting to change the workflow of an object
  and it has deleted children
  [ichim-david]

- Do not use portal_interface tool but @@plone_interface_info (PLIP #13770).
  [ale-rt]

- Internationalized file size and content type on file and image widgets.
  (needs Plone>=4.3.3)
  [thomasdesvenain]

- Make sure @@at_utils.translate method always returns a string (empty or
  not) even when the passed value is an empty tuple (before, the returned
  value was an empty tuple or a non empty string).
  [gbastien]

- Do not add warning about new field initialized on an existing object in
  the transaction description, show this as a Zope log info message.
  [gbastien]

- Move calendar_macros, jscalendar, and date_components_support here
  from CMFPlone and plone.app.form.
  [bloodbare, davisagli]

- Replace deprecated test assert statements.
  [timo]

- ``Vocabulary`` method was not working with ``vocabulary_factory``
  and int values (IntDisplayList is required)
  [keul]

- Remove code and tests for the old discussion infrastructure
  (pre plone.app.discussion). The discussion tool will be deprecated in
  Plone 5.
  [timo]

- Fix nesting-error in InAndOutWidget. This fixes
  https://github.com/plone/Products.Archetypes/pull/29
  [pbauer]

- Return original error during validation when a field already has an
  error.  This avoids ``TypeError: 'bool' object has no attribute
  '__getitem__'`` in ``Products.CMFFormController.ControllerState.``
  [maurits]

- Various vocabulary fixes, mostly for translations and
  IntDisplayLists.
  [maurits]

- Make (non-valued) default value selected in select widget if no selection
  is given. This happens  especially with ReferenceFields.
  [thepjot]
