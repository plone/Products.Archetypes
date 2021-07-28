Changelog
=========

.. You should *NOT* be adding new change log entries to this file.
   You should create a file in the news directory instead.
   For helpful instructions, please see:
   https://github.com/plone/plone.releaser/blob/master/ADD-A-NEWS-ITEM.rst

.. towncrier release notes start

1.16.5 (2021-07-28)
-------------------

Bug fixes:


- Fixed incompatibility with ``zope.component`` 5.
  ``zope.component.interfaces`` has long been a backwards compatibility import for ``zope.interface.interfaces``, but not anymore.
  [maurits] (#462)


1.16.4 (2021-01-08)
-------------------

Bug fixes:


- Lifted the ceiling for the maximum date from end of 2020 to 2051 in all places.
  See `issue 133 <https://github.com/plone/Products.Archetypes/issues/133>`_.
  [maurits] (#133)


1.16.3 (2020-10-30)
-------------------

Bug fixes:


- Lifted the ceiling for the maximum date from end of 2020 to 2051.
  See `issue 133 <https://github.com/plone/Products.Archetypes/issues/133>`_. (#133)


1.16.2 (2020-04-20)
-------------------

Bug fixes:


- Use manage_FTPget instead of manage_DAVget in marshall tests.
  Adds compatibility with Zope 4.3.
  [maurits] (#644)


1.16.1 (2019-05-06)
-------------------

Bug fixes:


- Problem: refactoring plone.app.widgets is not easy with too detailed expectations on the output of the pattern_options.
  Its also outside the scope of this test.
  Solution: check if there are pattern_options, but now what they are exactly.
  [jensens] (#124)
- Fixed slowness in ``unicodeTestIn`` script used by keyword template.
  [maurits] (#125)
- Fixed changelog for releases 1.15.5, 1.15.6 and 1.16.0.  [maurits] (#130)
- Fixed ``UnicodeEncodeError`` when editing Archetypes rich text.  [maurits] (#2832)


1.16.0 (2018-12-10)
-------------------

New features:

- Included ``__repr__`` changes from 1.15.5 again.  This change is only good for Plone 5.2.
  See also https://github.com/plone/Products.Archetypes/issues/130

Bug fixes:

- Fix packaging issues for Plone 5.2.
  [esteele]


1.15.6 (2018-12-10)
-------------------

Bug fixes:

- Reverted ``__repr__`` changes from 1.15.5.  That is only good for Plone 5.2.
  The 1.16.0 release will contain that change.


1.15.5 (2018-11-04)
-------------------

New features:

- Move generateUniqueId script from CMFPlone here.
  It has no use outside Archetypes world. (#114)
- Removed travis config. Jenkins is used instead. (#116)

Bug fixes:

- Fix testlayer mess.  [petschki] (#113)
- Use new utils.check_id from CMFPlone.  [maurits] (#118)
- Add ``PathReprProvider`` as a baseclass of ``BaseContentMixin`` to restore the original ``__repr__`` behavior instead of the new ``__repr__`` from ``persistent.Persistent``.
  See `issue 2590 <https://github.com/plone/Products.CMFPlone/issues/2590>`_.
  [pbauer] (#212)


1.15.4 (2018-09-30)
-------------------

Bug fixes:

- Switch to new TestCase using AT after PloneTestcase is now DX.
  Fall back to the old TestCase in case of an older plone.app.testing.
  [pbauer, maurits]


1.15.3 (2018-06-18)
-------------------

New features:

- Test against Plone 5.2
  [icemac]

Bug fixes:

- Fix Travis CI setup.
  [loechel]


1.15.2 (2018-05-03)
-------------------

Bug fixes:

- Make sure the 'at_ordered_refs' dict changes are persisted when setting
  references by manually setting '_p_changed=1'.
  [gbastien]

1.15.1 (2018-04-04)
-------------------

Bug fixes:

- Use the edit accessor to get text for TinyMCEWidget.
  [davisagli]

- Fixed html errors in documentation found with latest version of i18ndude.
  [vincentfretin]


1.15 (2018-02-05)
-----------------

New features:

- Removed CMFQuickInstaller dependency.
  This was only used in ancient migration code.
  [maurits]

Bug fixes:

- Fix test failures from https://github.com/plone/plone.app.widgets/pull/177
  [thet]


1.14.3 (2017-11-24)
-------------------

Bug fixes:

- Test fixes for changes in plone.app.widgets querystring options.
  [thet]

- Remove redefinition of builtin 'set' in a macro.
  [pbauer]

1.14.2 (2017-08-27)
-------------------

Bug fixes:

- Fixed textcount.js support jquery>1.6.
  [vkarppinen]

- Fixed a bug (that it was possible to enter text length over maxlimit)
  by replacing maxlimit alert() with highlighting textcountfield.
  [vkarppinen]

- Prevent AttributeError on deleting a Reference from a object that is gone.
  Fixes https://github.com/plone/plone.app.contenttypes/issues/41
  [pbauer]

- Remove Plone requirement on the testing extras.
  [gforcada]

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
