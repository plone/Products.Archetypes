====================================================
     HOWTO: Using Archetypes Custom Searching
====================================================

:Author: Joel Burton
:Contact: joel@joelburton.com
:Date: $Date$
:Version: $Revision: 1.3 $
:Web site: http://sourceforge.net/projects/archetypes
:Covers: Archetypes 1.2.1


.. contents::

Introduction
============

Archetypes includes generators for three kinds of widgets, view, edit,
and search.  The search widgets are widgets that are output for
customized search forms.

For example, imagine that you have an Archetypes object like::

  Schema = Schema (( StringField( 'countrycode', index='FieldIndex' ))

Archetypes will now keep your countrycode field in a Catalog, and you
can search the catalog using the ZCatalog API with the field
`countrycode`. To allow your users to search content by country code,
you'd want to include a text field on a search form where they can
type in the desired country code.

However, especially if you have many schemas, or the schemas can be
dnyamically changed by users (a feature demonstrated currently in
Andreas Jung's PloneCollectorNG, but coming to general Archetypes
soon), it's more convenient to have these search fields listed
automatically. This is what search widgets can do for us.


To Use
======

First, only fields that have the `index` property in a schema to
create an index are listed. This is sensible, as the searching
normally would be done with a Catalog call, so you'd need to have this
information catalogued.

Second, you should make sure that, if you've created and used any
custom widgets for these fields, that the widgets have a search macro
in their widget skin file.  The search macro will almost always be
exactly the same as the edit macro: if you enter the value in a text
box, it make sense to search for it that way; if you enter it in a
drop-down list, it makes sense to search using those restricted
choices.

Third, you'll need to create create a skin for the automatically
generated search view. You can add this to the bottom of any existing
search forms, or make a search for specifically for searching your
Archetypes objects.

The part of the search skin that calls the Archetypes API we need is::

  <div tal:define="errors python: {}">
    <tal:fields repeat="widget python: context.archetype_tool.getSearchWidgets()">
      <metal:fieldMacro use-macro="widget"/>
    </tal:fields>
  </div>

This will list search widgets for all Archetypes packages. If you want
search widgets just for a particular Archetypes package name, you
should change the `getSearchWidgets` call to
`getSearchWidgets(package="my_package_name")`. Also, you can specify a
single type to use with `type="my_type_name"`. This is useful to
create a search form for an individual packages or type, or to group
search controls on a shared search form by the packages or types.

This skin now, when viewed, will show the search widgets. You can wrap
this in an HTML form that calls your searching script, and unless you
have special needs, this could just call the standard CMF/Plone script
"search", giving you back results in a tabular list.


Example
=======

A good example of a product using this idea (and a good example for
advanced Archetypes examples in general) is PublisherInventory_.

.. _PublisherInventory: http://plone.org/newsitems/publisher-inventory-1.0


Notes
=====

This functionality was written in pre-1.0 Archetypes for a particular
client project, and seems to have been underused since. I'm not
certain if it works in Archetypes 1.0.x versions; however, I have
tested this with:

 * Plone 2.0rc2

 * Archetypes CVS HEAD

 * CMF 1.4.x

The current version of Archetypes (1.2.1) requires a one-line fix in
ArchetypeTool.py to use the getSearchWidgets() call; this has been
checked into the HEAD of the CVS, and, hopefully, by the time you read
this, should be in version 1.2.2 and later.

UPDATE: This is in Archetypes 1.2.2.


About this Document
===================

This document was written by `Joel Burton`_. It is covered under GNU
Free Documentation License, with one invariant section: this section,
`About this document`_, must remain unchanged. Otherwise, you can
distribute it, make changes to it, etc.

.. _`Joel Burton`: mailto:joel@joelburton.com

If you have any comments, corrections, or changes, please let me know.
Thanks!


.. target-notes::

    
..
   # vim:tw=70:ai:fo+=2
   Local Variables:
   mode: rst
   indent-tabs-mode: nil
   sentence-end-double-space: t
   fill-column: 70
   End:


