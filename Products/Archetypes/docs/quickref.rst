Archetypes Basic Reference
==========================

:Author: Sidnei da Silva
:Contact: sidnei@plone.org
:Date: $Date$
:Version: $Revision: 1.12 $
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

Although development is hosted at `plone.org`_'s `Subversion
repository`_, releases are still made available from the `Archetypes
Project`_ at `SourceForge`_.

.. _SourceForge: http://www.sourceforge.net
.. _Archetypes Project: http://sourceforge.net/projects/archetypes

The latest version of this document can be always found under the under
the `docs`_ directory of Archetypes.

.. _plone.org: http://plone.org
.. _Subversion repository: http://svn.plone.org
.. _docs: http://svn.plone.org/browse/archetypes/Archetypes/trunk/docs/

Use this command to checkout the most recent version of the project
anonymously::

  svn co http://svn.plone.org/archetypes/Archetypes/trunk Archetypes

This fetches the *trunk* of the package. For advice about the status of
the trunk and branches, see the `Plone developers' area`_.

.. _Plone developers' area: http://plone.org/development/info/

Installation
------------

Requirements
************

Archetypes is currently being tested and run in various environments
using the following combination:

- Zope 2.7.0

- Plone 2.x

- CMF 1.x

You should install the *PortalTransforms*, *MimetypeRegistry* and *validation* 
packages available in the archetypes repository (see above) before installing
Archetypes itself.
 
The easiest way to get all the necessary packages is to download the tarball 
made available upon release or check out the *bundle* from the repository to 
fetch the latest development release. For example, this is tarball containing 
the 1.3.1 release: ``Archetypes-1.3.1-final-Bundle.tgz``.

Using the tarball
*****************

1. Download the latest stable bundled version from `SourceForge`_.

2. Decompress it --- it should contain the following directories::

    Archetypes  MimetypesRegistry  PortalTransforms  validation

3. Copy these into the ``Products`` directory of your Zope installation.

4. Restart your Zope.

5. Check in the ``Control Panel`` of your Zope if everything imported
   just fine.

6. Good luck!


Checking out from SVN
*********************

You'll find recent information about the current state of SVN and 
instructions how to fetch the files in the 
`Download and SVN` section of Archetypes documentation on plone.org.

.. _Download and SVN: http://plone.org/documentation/archetypes/download


Schema
-------

The heart of an archetype is its ``Schema``, which is a sequence of
fields. Archetypes includes three stock schemas: *BaseSchema*,
*BaseFolderSchema*, and *BaseBTreeFolderSchema*. All three include two
fields, ``id`` and ``title``, as well as the standard metadata fields.

The ``Schema`` works like a definition of what your object will
contain and how to present the information contained. When Zope starts
up, during product initialization, Archetypes reads the schema of the
registered classes and automagically generates methods to access and
mutate each of the fields defined on a Schema.

Fields
------

You add additional fields to a schema by using one of the available
field types [#]_ . These fields share a set of properties (below, with
their default values), which you may modify on instantiation. Your
fields override those that are defined in the base schema.

.. [#] Field types included with Archetypes 1.3.0 are:
    BooleanField, CMFObjectField, ComputedField, DateTimeField,
    FileField, FixedPointField, FloatField, ImageField, IntegerField,
    LinesField, PhotoField, ReferenceField, StringField, TextField.

Commonly used field properties:

required
  Makes the field required upon validation. Defaults to 0 (not
  required).

widget
  One of the `Widgets`_ to be used for displaying and editing the
  content of the given field.

Less commonly used field properties:

default
  Sets the default value of the field upon initialization.

default_method
  Sets the default method called to obtain a value for the field upon
  initialization. The default method is specified as a string, which is
  found via (safe, non-acquiring!) attribute lookup on the instance.

vocabulary
  This parameter specifies a vocabulary. It can be given either
  as a static instance of ``DisplayList`` or as a method name (a string,
  found as above). The method is called and the result is taken as the
  vocabulary. The method should return a ``DisplayList``.

  The vocabulary instance or method supplies the values from which the
  value of this field may be selected.

  An example of ``DisplayList`` usage can be found in the
  ``ArchExample`` package (check it out from the `Subversion
  repository`_) in ``config.py``.
  ``Archetypes/ExtensibleMetadata.py`` also contains an example, which
  demonstrates passing ``msgid`` (for i18n purposes) to the
  ``DisplayList`` constructor.

enforceVocabulary
  If set, checks if the value is within the range of ``vocabulary`` upon
  validation.

multiValued
  If set, allows the field to have multiple values (e.g. a
  list) instead of a single value.

isMetadata
  If set, the field is considered metadata.

accessor [#]_
  Name of the method that will be used to return the value of the field,
  specified as a string. If the method already exists, nothing is done.
  If the method doesn't exist, Archetypes will generate a basic method
  for you.

edit_accessor
  Name of the method that will be used to return the value of the field
  *for editing purposes*. Unlike the standard accessor
  method which could apply some transformation to the accessed data,
  this method should return the raw data without any transformation.
  If the method already exists, nothing is done. If the method
  doesn't exist, Archetypes will generate a basic method for you.

  In this case the name of the method is generated by prepending
  ``getRaw`` (instead of just ``get``).

mutator
  Name of the method that will be used for changing the value
  of the field. If the method already exists, nothing is done. If the
  method doesn't exist, Archetypes will generate a basic method for you.

mode
  One of ``r``, ``w`` or ``rw``. If ``r``, only the accessor is
  generated. If ``w``, only the mutator and the edit accessor are
  generated. If ``rw``, accessor and mutator and edit accessor are
  generated.

  *Note*: ``r`` implies "human-readable", presented via the UI. The
  field is always readable from code via its *edit_accessor*.

read_permission
  Permission needed to view the field. Defaults to
  ``permissions.View``. Is checked when the view is being
  auto-generated.

write_permission
  Permission needed to edit the field. Defaults to
  ``permissions.ModifyPortalContent``. Is checked when the
  submitted form is being processed..

storage
  One of the `Storage`_ options. Defaults to
  ``AttributeStorage``, which just sets a simple attribute on the
  instance.

generateMode
  Deprecated?

force
  Deprecated?

validators
  One of the `Validators`_. You can also create your own validator. (See
  `Writing a custom validator`_.)

index
  A string specifying the kind of index to create on a catalog for this
  field. By default, indexes are created in ``portal_catalog``, but an
  alternative catalog may be used by beginning the string with the
  catalog name and a delimiting slash: ``member_catalog/FieldIndex``. 

  To include in catalog metadata, append ``:brains``, as in
  ``FieldIndex:brains``. You can specify another field type to try if
  the first isn't available by using the ``|`` character. All three
  combinations can be used together, as in::

    index="member_catalog/TextIndex|FieldIndex:brains",
   
  To index a field in multiple catalogs, specify the index as a tuple::

    index=("TextIndex|FieldIndex:brains",
           "member_catalog/TextIndex|FieldIndex:brains")

schemata
  Schemata is used for grouping fields into
  ``fieldsets``. Defaults to ``default`` on normal fields and
  ``metadata`` on metadata fields.


.. [#] Depending on the mode of each ``Field`` in the ``Schema`` the
   runtime system will look for an *accessor* and, possibly, a
   *mutator*. If, for example, the mode of a field is ``rw`` (the
   default), then the generator will ensure that the field has both an
   accessor and a mutator. This can happen in one of two ways: either
   you define the methods directly on your class, or you let the
   generator create them for you. If you don't require specialized
   logic, by all means let the generator create them. It keeps things
   consistent and uncluttered.

   The generated accessors and mutators are named by prepending ``get``
   (accessor) or ``set`` (mutator) to the (capitalised!) fieldname. For
   a field called ``fieldname``: 

   - accessor: ``getFieldname()`` (when called from a Page Template:
     ``context/getFieldname``)

   - mutator: ``setFieldname()``

   Fields are normally indexed under the name of their accessor.

   It is worth noting that Dublin Core metadata defines specific
   accessors that deviate from this rule by omitting the leading
   ``set``. See ``CMFCore/interfaces/DublinCore.py`` for these. 


Here is an example of a schema (from ``examples/SimpleType.py``)::

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

Watch out: if you define your schema like this and change anything in
``BaseSchema`` (hiding the ``id`` field, for example)::

  IdField = schema['id']
  IdField.widget.visible = {'edit': 'hidden', 'view': 'invisible'}

then you will hide the ``id`` field for **all** archetypes! To avoid
this, create your schema from a *copy* of the ``BaseSchema``::

  schema = BaseSchema.copy() + Schema((
  ...

Also note that the first argument passed to the ``Schema`` constructor
must always be a *tuple* of fields. Remember the trailing comma if
you're only adding a single field, as in the example above!


Validators
----------

Archetypes provides some pre-defined validators in the ``validation``
package. You specify validators for a field by passing a tuple of
strings in the ``validators`` field property, each string being the name
of a validator. [#]_ Most of the default validators are simply
regular-expression based, and not that rigorous. The validators and the
conditions they test are:

BaseValidators
**************

inNumericRange
  The argument must be numeric. The validator should be called with the
  minimum and maximum values as second and third arguments. 

isDecimal
  The argument must be decimal, may be positive or
  negative, may be in scientific notation.

isInt
   The argument must be an integer, may be positive or negative.

isPrintable
  The argument must only contain one or more
  alphanumerics or spaces.

isSSN
  The argument must contain only nine digits (no separators) (Social
  Security Number). (This one is pretty lame.)

isUSPhoneNumber
  The argument must contain only 10 digits (no separators). (Lame.)

isInternationalPhoneNumber
  The argument must contain only one or
  more digits (no separators). (Lame.)

isZipCode
  The argument must contain only five or nine digits (no
  separators).

isURL
  The argument must be a valid URL (including protocol, no
  spaces or newlines). (Lame.)

isEmail
  The argument must be a valid email address.

isUnixLikeName
  The argument starts with a letter, and continues with between 0 and 7
  alphanumerics, dashes or underscores.


EmptyValidator
**************

isEmpty
  The argument must be empty (where *empty* may be defined by a marker
  that is passed in and optionally returned). By default, the marker is
  ``[]`` and it is returned.

isEmptyNoError
  ``isEmpty`` fails with an error message, but ``isEmptyNoError`` just
  fails.


SupplValidators
***************

isMaxSize
  Tests if an upload, file or something supporting len() is smaller than
  a given max size value.

isValidDate
  The argument must be a ``DateTime`` or a string that converts to a
  ``DateTime``.

ATContentTypes provides some more validators.


The current usefulness of Archetypes' validators is mitigated by weak
error messaging, and the lack of support for separators in SSNs, phone
numbers, and ZIP codes.

There are also hooks for pre and post validation that can be used to
assert things about the entire object. These hooks are::

  pre_validate(self, REQUEST, errors)
  post_validate(self, REQUEST, errrors)

To use them, define methods with those names on your class. You must
extract values from ``REQUEST`` and write values into ``errors`` using
the field name as the key. If ``pre_validate`` throws errors, then other
custom validators (including ``post_validate``) will not be called.


.. [#] Right now the ``validators`` field option supports different types:

       - The *name* of an registered validator

       - A registered or unregistered *instance* implementing IValidator

       - A *validator chain* object

       - A *list or tuple* of strings, validators or validator chains

       - A validator may be specified as a singleton or a two-tuple, in
         which case the second element is an argument for the validator.
         The default value is *required*::

          validators = (('isEmpty', V_SUFFICIENT), 'isURL')


Writing a custom validator
**************************

If you need custom validation, you can write a new validator in your product.::

    from Products.validation.interfaces import ivalidator
    from zope.interface import implements
    class FooValidator:
        implements(ivalidator)
        def __init__(self, name):
            self.name = name
        def __call__(self, value, *args, **kwargs):
            if value != 'Foo':
                return ("Validation failed(%s): value is %s"%(self.name,
                    repr(value)))
            return 1

Then you need to register it, for example in the ``initialize`` method
``FooProduct/__init__.py``::

    from Products.validation import validation
    from validator import FooValidator
    validation.register(FooValidator('isFoo'))

The validator is now registered, and can be used in the schema of your type.

Note: make sure that your validator is registered before any code is
called that wants to use this validator, most likely in the schema of
a content type.  If you see this when Zope starts up::

    WARNING: Disabling validation for <field name>: <your validator>

then you are registering your validator too late.


Widgets
-------

When Archetypes generates a form from a schema, it uses one of the
available Widgets for each field. You can tell Archetypes which widget
to use for your field using the ``widget`` field property. Note,
though, that a field cannot use just any widget, only one that yields
data appropriate to its type. Below is a list of possible widget
properties, with their default values (see ``generator/widget.py``).
Individual widgets may have additional properties.

description
  Some documentation for this field. It's rendered as a ``div`` with the
  CSS class ``formHelp``.

label
  Is used as the label for the field when rendering the form.

visible
  Defaults to ``{'edit':'visible', 'view':'visible'}``, which signifies
  that the field should be visible in both *edit* and *view* modes.
  Other possible values are ``hidden`` (include on the form, but as a
  *hidden* control) and ``invisible`` (skip rendering).

  There is a shorthand to define visibility for all modes at once::

    visible = True  # (or 1): 'visible'
    visible = False # (or 0): 'invisible'
    visible = -1    # 'hidden'


Views
-----

Views are auto-generated for you by default, based on the options you
specified on your ``Schema`` (Widgets, Fields, widget labels, etc.) if
you use the default FTI (Factory Type Information) actions (that is, if
you don't provide an ``actions`` attribute in your class. See
`Additional notes about Factory Type Information`_).


Customizing Views
*****************

If you want only to override a few parts of the
generated View, like the header or footer, you can:

1. Create a template named ``${your_portal_type_lowercase}_view`` [#]_

   .. [#] Currently, this is only implemented for the auto-generated
       ``view`` template.

2. On this template, you may provide the following macros::

     header
     body
     footer

3. When building the auto-generated view, archetypes looks for
   these macros and includes them in the view, if available. Note that
   the ``body`` macro overrides the auto-generated list of
   fields/values.

Or, for customizing only a widget:

1. Set the attribute ``macro`` to the location of a page template
   containing the macros for rendering the Widget.

2. Your custom macro template must contain macros with the same names
   as the modes in which it will be used (e.g. ``view``, ``edit``, and
   ``search``).

3. If you're reusing an existing widget but you want to customize *only*
   the rendering for a particular mode, you can set attributes such as
   ``macro_view`` or ``macro_edit`` to the location of a page template
   containing a macro for the corresponding mode.


Class Attributes
----------------

Besides the schema, you can define all of the content properties you
see when you click on a content type in the ``portal_types`` tool in the
ZMI. Here is a list of class attributes, with their default values (see
``ArchetypeTool.py``):


Default class attributes/methods
********************************

modify_fti : method
  Is looked up on the module and called before product
  registration. Works as a hook to allow you to modify the standard
  ``factory type information`` provided by Archetypes.

add${classname} : method
  Is looked up on the module. If it doesn't exist, a basic one is
  autogenerated for you.

content_icon
  A name of an image (that must be available in the context of your
  object) to be used as the icon for your content type inside CMF and
  Plone.

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

- Custom actions: Define an ``actions`` member on your content type, and
  the external method will apply this to the types tool for you. These
  actions **extend** or **replace** any existing actions for your type.
  If you want to delete or rearange actions, you need to manipulate
  ``fti['actions']`` in the ``modify_fti`` method of your module. 

  This means that if you want custom views or something you only need to
  say something like::

      class Foo(BaseContent):
          actions = ({'id': 'view',
	                  'name': 'View',
                      'action': 'string:${object_url}/custom_view',
                      'permissions': (permissions.View,)
                     },)


Storage
-------

There are a few basic storages available by default on Archetypes,
including storages that store data using SQL. Here's a listing:

AttributeStorage
  Simply stores the attributes right into the instance.

MetadataStorage
  Stores the attributes inside a ``PersistentDict`` named ``_md`` in
  the instance.

ReadOnlyStorage
  Used to mark a field as being ``ReadOnly``

ObjectManagedStorage
  Uses the ``ObjectManager`` methods to keep the attribute inside the
  instance. Allows you to make a folderish content object behave like a
  simple content object.

``*SQLStorage``
  Experimental storage layer, which puts the data inside an RDBMS using
  SQL. Available variations are: MySQL and PostgreSQL. There's an initial
  implementation of an Oracle storage, but it isn't tested at the
  moment.

Marshall
--------

From The Free On-line Dictionary of Computing (09 FEB 02) [foldoc]:

  marshalling

     <communications> (US -ll- or -l-) The process of packing one
     or more items of data into a message {buffer}, prior to
     transmitting that message buffer over a communication channel.
     The packing process not only collects together values which
     may be stored in non-consecutive memory locations but also
     converts data of different types into a standard
     representation agreed with the recipient of the message.

Marshalling is used in Archetypes to convert data into a single file
for example, when someone fetches the content object via FTP or
WebDAV. The inverse process is called *demarshalling*.

Archetypes currently has a few sample marshallers, but they are
somewhat experimental (there are no tests to confirm that they work,
and that they will keep working). One of the sample marshallers is the
``RFC822Marshaller``, which does a job very similar to what CMF does
when using FTP and WebDAV with content types. Here's what happens:

1. Find the primary field for the content object, if any.

2. Get the content type for the primary field and its content.

3. Build a dict with all the other fields and its values.

4. Use the function ``formatRFC822Headers`` from ``CMFDefault.utils`` to
   encode the dict into RFC822-like fields.

5. Append the primary field content as the body.

6. Return the content_type, length and data.

When putting content back, the inverse is done:

1. The body is separated from the headers, using ``parseHeadersBody``
from ``CMFDefault.utils``.

2. The body, with the content type, is passed to the mutator of the
primary field.

3. For each of the headers, we call the mutator of the given matching
field with the header value.

That's it.


An example of using a Marshaller
********************************

To use a Marshaller, you just need to pass a Marshaller instance as
a keyword argument of the Schema. For example::

    from Products.Archetypes.Marshall import RFC822Marshaller
    class Story(BaseContent):
        schema = BaseSchema + Schema ((

            TextField('story_description',
                      primary = 1,
                      default_output_type = 'text/plain',
                      allowable_content_types = ('text/plain', 'text/restructured',),
                widget = TextAreaWidget(label = 'Description',
                                        description = 'A short story.'
                                        )),

            ),
            marshall = RFC822Marshaller())


Examples and more information
-----------------------------

Examples can be found on the ArchExample product. You can also `browse
the Subversion repository`_.

.. _browse the Subversion repository: http://svn.plone.org/browse/archetypes/Archetypes/trunk


Special Thanks
--------------

To Vladimir Iliev, for contributing with i18n and lots of other nice
ideas and Bill Schindler, for lots of nice patches and reviewing documentation.


..
   Local Variables:
   mode: rst
   indent-tabs-mode: nil
   sentence-end-double-space: t
   fill-column: 70
   End:

