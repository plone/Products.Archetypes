Archetypes Basic Reference
==========================

:Author: Sidnei da Silva
:Contact: sidnei@x3ng.com
:Date: $Date: 2003/05/13 20:36:37 $
:Version: $Revision: 1.2 $
:Web site: http://sourceforge.net/projects/archetypes

.. contents::

Introduction
------------

Archetypes is a framework for developing new content types in
Plone. The power of Archetypes is, first, in automatically generating
forms; second, in providing a library of stock field types, form
widgets, and field validators; third, in easily integrating custom
fields, widgets, and validators; and fourth, in automating
transformations of rich content.

The project is hosted on the `Archetypes Project`_ at
`SourceForge`_. Other sources of information include the documentation
included in the download under the `docs`_ directory.

.. _SourceForge: http://www.sourceforge.net
.. _Archetypes Project: http://sourceforge.net/projects/archetypes
.. _docs: .

Installation
------------

Using the tarball
*****************

1. Download the latest stable version from the `Archetypes Project`_
   on `Sourceforge`_.

2. Decompress it into the ``Products`` dir of your Zope
   installation. It should contain the following directories::

     Archetypes
     ArchExample
     transform
     validation
     generator

3. Restart your Zope.

4. Check in the ``Control Panel`` of your Zope if everything imported
   just fine.

5. Good luck!

Checking out from CVS
*********************

Using Windows
#############

If you want to get the latest version of Archetypes from CVS, here is
how to do it.

1. Get TortoiseCVS from http://prdownloads.sourceforge.net/tortoisecvs/TortoiseCVS-1-2-2.exe

2. Download and install the program.

3. Reboot if necessary.

XXX Need more info here.

Using ``*nix``
##############

Quick and dirty::

  cvs -d:pserver:anonymous@cvs.sourceforge.net:/cvsroot/archetypes login
  cvs -z3 -d:pserver:anonymous@cvs.sourceforge.net:/cvsroot/archetypes co Archetypes
  cvs -z3 -d:pserver:anonymous@cvs.sourceforge.net:/cvsroot/archetypes co ArchExample
  cvs -z3 -d:pserver:anonymous@cvs.sourceforge.net:/cvsroot/archetypes co validation
  cvs -z3 -d:pserver:anonymous@cvs.sourceforge.net:/cvsroot/archetypes co generator
  cvs -z3 -d:pserver:anonymous@cvs.sourceforge.net:/cvsroot/archetypes co transform


Schema
-------

The heart of an archetype is its ``Schema``, which is a sequence of
fields. Archetypes includes three stock schemas: BaseSchema,
BaseFolderSchema, and BaseBTreeFolderSchema. All three include two
fields, 'id' and 'title', as well as the standard metadata fields.

The ``Schema`` works like a definition of what your object will
contain and how to present the information contained. When Zope starts
up, during product initialization, Archetypes reads the schema of the
registered classes and automagically generates methods to access and
mutate each of the fields defined on a Schema.

Fields
------

You add additional fields to a schema by using one of `available field
types`. These fields share a set of properties (below, with their
default values), which you may modify on instantiation. Your fields
override those that are defined in the base schema.

More commonly used field properties:

required
  Makes the field required upon validation. Defaults to 0
  (not required).

widget
  One of the `Widgets`_ to be used for displaying
  and editing the content of the given field.

Less commonly used field properties:

default
  Sets the default value of the field upon initialization.

vocabulary
  A set of values (usually a ``DisplayList``) which can be
  choosen from to fill this field.

enforceVocabulary
  If set, checks if the value is within the range
  of ``vocabulary`` upon validation

multiValued
  If set allows the field to have multiple values (eg: a
  list) instead of a single one

isMetadata
  If set, the field is considered metadata

accessor [#]_
  Name of the method that will be used for getting data out
  of the field. If the method already exists, nothing is done. If the
  method doesnt exists, Archetypes will generate a basic method for you.

mutator
  Name of the method that will be used for changing the value
  of the field. If the method already exists, nothing is done. If the
  method doesnt exists, Archetypes will generate a basic method for you.

mode
  One of ``r``, ``w`` or ``rw``. If ``r``, only the accessor is
  generated. If ``w`` only the mutator is generated. If ``rw``, both
  the accessor and mutator are generated.

read_permission
  Permission needed to view the field. Defaults to
  CMFCorePermissions.View. Is checked when the view is being auto-generated.

write_permission
  Permission needed to view the field. Defaults to
  CMFCorePermissions.ModifyPortalContent. Is checked when the
  submitted form is being processed..

storage
  One of the `Storage`_ options. Defaults to
  ``AttributeStorage``, which just sets a simple attribute on the instance.

generateMode
  Deprecated?

force
  Deprecated?

validators
  One of the `Validators`_. You can also create your own validator.

index
  A string specifying the kind of index to create on
  ``portal_catalog`` for this field. To include in catalog metadata,
  append ``:schema``, as in ``FieldIndex:schema``. You can specify
  another field type to try if the first isn't available by using the
  ``|`` character. Both combinations can be used together, as in::

    ...
    index="TextIndex|FieldIndex:schema",
    ...

schemata
  Schemata is used for grouping fields into
  ``fieldsets``. Defaults to ``default`` on normal fields and
  ``metadata`` on metadata fields.

Here is an example of a schema (from 'examples/SimpleType.py')::

  schema = BaseSchema + Schema((
    TextField("body",
          required=1,
          searchable=1,
          default_output_type="text/html",
          allowable_content_types=("text/plain",
                                   "text/restructured",
                                   "text/html",
                                   "application/msword"),
          widget  = RichWidget,
          ),
    ))


.. [#] Depending on the mode of each Field in the Schema the runtime system
   will look for an accessor or mutator. If for example the mode of a field is
   "rw" (as is the default) then the generator will ensure that accessors and
   mutators exist for that field. This can happen one of two ways, either as a
   developer you define the methods directly on your class, or you let the
   generator provide them for you. If you don't require specialized logic then
   letting the generator create these methods on your new type is a good idea.

   The format for accessors and mutators is as follows::

     field -> title

     accessor -> getTitle()          here/getTitle
     mutator  -> setTitle(value)


Widgets
-------

When Archetypes generates a form from a schema, it uses one of the
available Widgets for each field. You can tell Archetypes which widget
to use for your field using the ``widget`` field property. Note,
though, that a field cannot use just any widget, only one that yields
data appropriate to its type. Below is a list of possible widget
properties, with their default values (see 'generator/widget.py').
Individual widgets may have additional properties.

attributes
   Used for??

description: The tooltip for this field. Appears onFocus.

description_msgid
  i18n id for the description

label
  Is used as the label for the field when rendering the form

label_msgid
  i18n id for the label

visible
  Defaults to 1. Use 0 to render a hidden field, and -1 to skip rendering.

Validators
----------

Archetypes also provides some validators. You use them by
passing a sequence of strings in the ``validator`` field property, each
string being a name of a validator. The validators and the conditions
they test are:

inNumericRange
  The argument must be numeric

isDecimal
  The argument must be decimal, may be positive or
  negative, may be in scientific notation

isInt
   The argument must be an integer, may be positive or negative

isPrintable
  The argument must only contain one or more
  alphanumerics or spaces

isSSN
  The argument must contain only nine digits (no separators) (Social
  Security Number?)

isUSPhoneNumber
  The argument must contain only 10 digits (no separators)

isInternationalPhoneNumber
  The argument must contain only one or
  more digits (no separators)

isZipCode
  The argument must contain only five or nine digits (no
  separators)

isURL
  The argument must be a valid URL (including protocol, no
  spaces or newlines)

isEmail
  The argument must be a valid email address

The current usefulness of Archetypes' validators is mitigated by weak
error messaging, and the lack of support for separators in SSNs, phone
numbers, and ZIP codes.

There are also hooks for pre and post validation that can be used to
assert things about the entire object, these are as follows::

  pre_validate(self, REQUEST, errors)
  post_validate(self, REQUEST, errrors)

You must then extract values from ``REQUEST`` and write values into ``errors``
with the field name as the key. If ``pre_validate`` throws errors then
other custom validators (including post) will not be called.

Writing a custom validator
**************************

If you need custom validation, you can write a new validator in your product.::

    from Products.validation.interfaces import ivalidator
    class FooValidator:
        __implements__ = (ivalidator,)
        def __init__(self, name):
            self.name = name
        def __call__(self, value, *args, **kwargs):
            if value == 'Foo':
                return """Validation failed"""
            return 1

Then you need to register it in FooProduct/__init__.py method initialize::

    from Products.validation import validation
    from validator import FooValidator
    validation.register(FooValidator('isFoo'))

The validator is now registered, and can be used in the schema of your type.

Class Attributes
----------------

Besides the schema, you can define all of the content properties you
see when you click on a content type in the 'portal_types' tool. Here
is a list of class attributes, with their default values (see
'ArchetypeTool.py'):

Default class attributes/methods
********************************

modify_fti : method
  Is looked up on the module and called before product
  registration. Works as a hook to allow you to modify the standard
  ``factory type information`` provided by Archetypes.

add${classname} : method
  Is looked up on the module. If it doesnt exist, a basic one is
  autogenerated for you.

content_icon
  A name of an image (that must be available in the context of your
  object) to be used as the icon for your content type inside CMF.

global_allow
  Overrides the default ``global_allow`` setting on the default
  factory type information.

allowed_content_types
  Overrides the default ``allowed_content_types`` setting on the default
  factory type information. If set, supercedes the
  ``filter_content_types`` in case it is not provided on the class.

filter_content_types
  Overrides the default ``filter_content_types`` setting on the default
  factory type information.

Additional notes about Factory Type Information
***********************************************

- If your class declares to implement ``IReferenceable``, you will get a
  ``references`` tab on your object, allowing you to make references to
  other objects.

- If your class declares to implement ``IExtensibleMetadata``, you will get a
  ``properties`` tab on your object, allowing you to modify the metadata.

- Custom actions: Define an actions member on your content type and
  the external method will apply this to the types tool for you. This
  means the if you want custom views or something you only need to say something like::

      class Foo(BaseContent):
          actions = ({'id': 'view',
	              'name': 'View',
                      'action': 'custom_view',
                      'permissions': (CMFCorePermissions.View,)
                     },)


Storage
-------

There are a few basic storages available by default on Archetypes,
including storages that store data on SQL. Heres a listing:

AttributeStorage
  Simply stores the attributes right into the instance.

MetadataStorage
  Stores the attributes inside a ``PersistentDict`` named ``_md`` in
  the instance.

ReadOnlyStorage
  Used to mark a field as being ``ReadOnly``

ObjectManagedStorage
  Uses the ``ObjectManager`` methods to keep the attribute inside the
  instance. Allows to make a folderish content object behave like a
  simple content object.

``*SQLStorage``
  Experimental storage layer, which puts the data inside
  SQL. Available variations are: MySQL and PostGRES. Theres a initial
  implementation of a Oracle storage, but it isn't tested at the
  moment.

How to write your own SQLStorage
********************************

XXX Not written yet.

Views
-----

Views are auto-generated for you by default, based on the options you
specified on your ``Schema`` (Widgets, Fields, widget labels, etc.) if
you use the default FTI actions (eg: dont provide an ``actions``
attribute in your class. See `Additional notes about Factory Type
Information`_). 

Customizing Views
*****************

If you want only to override a few parts of the
generated View, like the header or footer you can:

1. Create a template named ``${your_portal_type_lowercase}_view`` [#]_

2. On this template you may provide the following macros::

     header
     body
     footer

3. When building the auto-generated view, archetypes will look for
   these macros and include them in the view if available. Note that
   the body macro overrides the auto-generated list of fields/values.

.. [#] Currently, this is only implemented for the auto-generated
   ``view`` template.

or, for customizing only a widget:

1. Set the attributes ``macro_view`` or ``macro_edit`` to the location
   of your custom macro upon instantiation of the Widget.

2. Your custom macro template must contain a macro with the same name
   as the mode where it will be used. Eg: a template that is being
   used on ``macro_view`` must have a macro named ``view``. The same
   applies to ``macro_edit`` and ``edit``.



..
   Local Variables:
   mode: rst
   indent-tabs-mode: nil
   sentence-end-double-space: t
   fill-column: 70
   End:
