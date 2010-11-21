====================================================
HOWTO: Using Archetypes SQLStorage and Advanced Tips
====================================================

:Author: Joel Burton
:Contact: joel@joelburton.com
:Date: $Date$
:Version: $Revision: 1.2 $
:Web site: http://sourceforge.net/projects/archetypes
:Covers: Archetypes 1.0beta

.. epigraph::

  Where is the knowledge we have lost in information?

  -- T. S. Eliot, *The Rock*

.. contents::

Introduction
============

The SQLStorage storage for Archetypes_ allows you to transparently
store attributes of your Archetypes objects in an SQL-backed database.

This is useful in many situations, such as:

- You have other applications that need to simultaneous access data in
  relational database format.

- You have a lot of existing data in a relational database format.

- You or your boss/client are more comfortable knowing that your data
  is accessible in a relational database format.

This HOWTO assumes that you are comfortable installing Archetypes, and
using it with non-SQLStorage, and are comfortable administering
Plone/CMF/Zope sites.

This HOWTO explains how you can use relational database features like
triggers and rules to store your data in traditional relational
database parent/child tables, while still accessing it with
traditional Zope accessors.  While the advanced techniques in this
HOWTO can be used with any database that supports triggers and
updatable views, the example code is for PostgreSQL_. It should not be
difficult to translate these ideas to Oracle or other database.  At
the time of this writing, MySQL does not support triggers, views, or
rules, so these ideas could not easily be implemented in MySQL.

.. _PostgreSQL: http://www.postgresql.org

.. _Archetypes: http://www.sf.net/projects/archetypes


Typographic conventions
-----------------------

In most relational databases, commands are case-insensitive: `SELECT`
is the same as `select`. To help you understand the commands, however,
I'll follow the traditional format of putting SQL commands in upper
case.

Database identifiers (field names, table names, etc.) may or may not
be case-sensitive, depending on your database. The examples here will
be using PostgreSQL, which is case-insensitive for identifiers. I'll
show table names with a leading capital letter, and field name in all
lower case. However, you can enter these any way you like.



Comparing SQLStorage to other relational database interface strategies
----------------------------------------------------------------------

The scope of what Archetypes accomplishes is similar to, yet very
different from, other systems of connecting Zope to relational
databases.

Archetypes stores the objects in the ZODB as an archetype object,
having traditional Plone/CMF/Zope methods such as `Title()`,
`absolute_url()`, etc. However, individual attributes (such as title,
author, body, etc.) can be looked up in and stored in the relational
database. Since objects are real Zope objects, they work naturally
with acquisition, catalogs, and other Zope technologies.  Since you
can choose which attributes to store in the relational database,
attributes that don't have a naturally tight fit with relational
database structures can be left in the ZODB, as can ones that might
easily fit in a relational database structure, but for which you have
no external relational database access requirements.


Versus ZSQL methods
+++++++++++++++++++

A more traditional method of Zope/Relational Database connection has
been to store rows of information in a relational database, and create
ZSQL Methods to look up and display this information. With this
technique, you can associate a Python class with a relational database
row [#]_, but the objects aren't real persistent Zope objects, and
aren't found during catalog calls. This strategy requires customized
integration to work with key Plone technologies such as acquisition,
workflow, portal_forms, etc.

While there are worthwhile Zope product to simplify some of the
details of traditional relational database storage and Zope (such as
Znolk_, which auto-generates database forms and storage methods),
these still fall quite short of the interface simplication and power
that Archetypes delivers.

Traditional SQL Method strategies for using Zope with relational
databases are of most use when converting an existing site built using
other web technologies (such as PHP or Perl), and in which you already
have written the SQL statements for insterting, updating, deleting,
viewing, etc., all of your object types.

.. _Znolk: http://www.bluedynamics.org/products/znolk

.. [#] This technique goes by the colorful name *pluggable brains*.


Versus APE (formerly Adaptable Storage)
+++++++++++++++++++++++++++++++++++++++

Shane Hathaway's product APE_ (formerly called Adaptable Storage)
allows you to store your Zope objects in different formats (such as in
standard filesystem objects or on a relational database). In this
case, segments of the ZODB space are "mounted" from results in a
relational database. This means the entire object is kept in the
relational database--all attributes, etc.  Deleting an object from the
relational database, adding it, or modifying it affects the the ZODB
instantly since the this part of the ZODB is just a mounted pointer
the relational database.

While APE is a technological accomplishment, and very useful for some
projects, it doesn't fit perfectly into an existing natural database
role. All ZODB objects are stored in a few very APE-oriented tables,
rather than being stored in customizable,
traditional-relational-database tables. 

In addition, APE works by location, rather than by type (as Archetypes
does).  That is, *everything* in the folder `/foo` is controlled
(mounted) by APE. If `/foo` contains all and only objects of a certain
portal_type (like Customers) you could treat these tables as the
"customer relational database", and work around the unusual
object-to-relational database table structure. However, if there are
different types stored in that directory, you end up with a mishmash
of different types of data stored in the same tables, and don't have
the straightforward setup of a "customer" table versus an "orders"
table, etc.  [#]_ With Archetypes, each portal_type maps to an
individual table, regardless of where it is stored.

Lastly, APE does not produce the integrated form
production/validation/editing systems that Archetypes does.

.. _APE: http://hathaway.freezope.org/Software/Ape

.. [#] It seems as if APE supports custom object marshallers and
   unmarshallers to create different table types for different object
   types; however, at this point, I haven't been able to find working
   examples of this that I could understand and apply.


Creating a Database-Stored Object
=================================

Let's start with a simple Archetypes object, representing a Customer::

  # Customer.py
  # Customer portal type (non-SQL storage)

  from Products.Archetypes.public import *
  from Products.Archetypes.TemplateMixin import TemplateMixin

  schema = BaseSchema + Schema((
      
      TextField('body',
                required=1,
                primary=1,
                searchable=1,
                default_output_type='text/html',
                allowable_content_types=('text/restructured',
                                         'text/plain',
                                         'text/html',
                                         'application/msword'),
                widget=RichWidget,
                ),
      
      StringField("phone",
                   index="FieldIndex",
                   ),
      
      )) + TemplateMixin.schema

  class Customer(TemplateMixin, BaseContent):
      """Our example object"""
      schema = schema
      archetype_name = "Customer"
      actions = TemplateMixin.actions
                    
  registerType(Customer)

This object defines two custom fields, `body` and `phone` (plus all
the traditional metadata attributes that are brought in by
`BaseSchema`). This object would be stored entirely in the ZODB by
Archetypes; however, we can convert this to being stored in a
relational database by making just two simple changes to the object:

- Add an import to the beginning for the appropriate SQL database
  storage method.

- Add an attribute `storage` to the fields we want stored in the
  database, and set these to our storage method.

Since we're using PostgreSQL in this example, we'll import the
PostgreSQL storage method.

Our new object then becomes::

  # CustomerSQL.py
  # Customer portal type (SQL storage)

  from Products.Archetypes.public import *
  from Products.Archetypes.TemplateMixin import TemplateMixin
  from Products.Archetypes.SQLStorage import PostgreSQLStorage

  schema = BaseSchema + Schema((
      
      TextField('body',
                required=1,
                primary=1,
                searchable=1,
                storage=PostgreSQLStorage(),
                default_output_type='text/html',
                allowable_content_types=('text/restructured',
                                         'text/plain',
                                         'text/html',
                                         'application/msword'),
                widget=RichWidget,
                ),
      
      StringField("phone",
                  storage=PostgreSQLStorage(),
                  index="FieldIndex",
                  ),
      
      )) + TemplateMixin.schema

  class CustomerSQL(TemplateMixin, BaseContent):
      """Our example object"""
      schema = schema
      archetype_name = "Customer SQL"
      actions = TemplateMixin.actions
                    
  registerType(CustomerSQL)

At this point, you should install our new Archetypes type and register
it with portal_types.

Now, before we can begin using this object, we must do two things:

- Add a database connector (in our case, PostgreSQL) to our site. We
  can use any PostgreSQL adapter; however, I've used ZPyscopgDA_ for
  testing this, as this appears to be the best maintained of the
  noncommercial adapters.

.. _ZPyscopgDA: http://initd.org/software/psycopg

- In the `archetype_tool`, under the `Connections` tab, we need to set
  our database connector for this type of object to our new database
  connector.  Note that in this tab, we have a `default` connection,
  and we can override this for an portal_type that uses SQLStorage. In
  our case, you can either set the default to the new connection, or
  the specific connection for our `CustomerSQL` type. However, since
  we'll be adding several other Archetypes types, it will be easier to
  point the `default` setup to your database adapter connection.

Before you go any further, make sure that the user you defined in your
database connection has the ability to create tables, and insert,
update, and delete from tables in your database. [#]_

.. [#] In real life, it isn't neccessary that the user have to have
   `CREATE TABLE` privileges, as you can create the table yourself
   before Archetypes tries to. However, it's easiest to let Archetypes
   create the table for you. In which case a good strategy is to grant
   `CREATE TABLE` permissions for the zope database connector user,
   let it create the table, then rescind that right (for security's
   sake) once the table has been created.


Testing Our New Object
======================

Now, we can add an instance of our object through the standard Plone
interface. Plone will recommend a unique ID; let's change that to
"new_example". Put in values for `body` and `phone`. Notice that you
can see these values in the `view` view, and can re-edit them in the
`edit` view.

Switch to your database monitor (for PostgreSQL, this is `psql`) and
examine the database:

.. parsed-literal::

  database=# **\\d**
                    List of relations
   Schema |           Name           |   Type   | Owner
  --------+--------------------------+----------+-------
   public | customersql              | table    | joel

Archetypes has created our table for us. Examine the table:

.. parsed-literal::

  database=# **\\d customersql**
    Table "public.customersql"
    Column   | Type | Modifiers
  -----------+------+-----------
   uid       | text | not null
   parentuid | text |
   body      | *text* |
   phone     | *text* |
  Indexes: customersql_pkey primary key btree (uid)

Notice that Archetypes has created our `body` field as text field and
the `phone` field as a text field. These transformations are part of
the PostgreSQLStorage method, and can be easily changed in the source,
should your needs require different mappings. [#]_ We'll look at
changing those mappings later in this document, in `Changing
SQLStorage's Storage Methods: An Example With Lists`_.

Also, notice that there are two new fields created:

- **UID** (`uid`): this is a unique identifier for your object

- **Parent UID** (`parentuid`): this is the unique identifier (if any)
  for the parent (enclosing) container for your object.


.. [#] Or you can create the table in advanced of Archetypes, and
   choose whatever field types you want, as long as your database can
   cast Archetypes values into your field types. For instance, in our
   example, though `text` is an acceptable choice for phone numbers,
   we might prefer to have this stored as a `varchar(20)`.  We could
   have created the table ourselves and made this choice; when
   Archetypes goes to insert a `text`-type value into phone,
   PostgreSQL can cast this to `varchar(20)`


About UIDs
==========

One of the smartest things about Archetypes is that it introduces the
ideas of unique identifiers into CMF sites. Zope IDs must be unique
within a folder, but need not be unique across a site. Therefore,
keeping track of the fact that you have an object called `Milo` isn't
useful, since you may have several objects called that in different
folders.

A common workaround has been to refer to objects by their path (eg,
`/animals/cats/Milo`), but this is fragile, since any change to the
object ID, or the IDs of any of the parent objects will change the
path and break these references.

Archetypes assigns each object a unique ID at creation [#]_, and then
maintains a mapping of that unique ID to the current location of the
object in the ZODB.  If the object is deleted, Archetypes will remove
it from its UID mapping.

.. [#] The IDs that are created are in the Plone default style, e.g.,
   PortalType.2003-07-23.4911

Please note the difference between the Zope ID (the standard name for
the object returned by `getId()`) and the Archetypes UID. When our
object was created, Plone assigned it an ID like
`CustomerSQL.2003-07-23.4911`. Archetypes used this ID as its UID.
Even though we may change the object *ID* to `new_example`, it will
keep its *UID* for the lifetime of the object. The UID should be
treated as an immutable attribute.

Archetypes also creates a `portal_catalog` index for the UID field, so
you can easily query the catalog using the UID. It also exposes
several methods in its API for finding an object by its UID (from
ArchetypeTool.py)::

    ## Reference Engine Support
    def lookupObject(self, uid):
        if not uid:
            return None
        object = None
        catalog = getToolByName(self, 'portal_catalog')
        result  = catalog({'UID' : uid})
        if result:
            #This is an awful workaround for the UID under containment
            #problem. NonRefs will aq there parents UID which is so
            #awful I am having trouble putting it into words.
            for object in result:
                o = object.getObject()
                if o is not None:
                    if IReferenceable.providedBy(o):
                        return o
        return None

    def getObject(self, uid):
        return self.lookupObject(uid)

    def reference_url(self, object):
        """Return a link to the object by reference"""
        uid = object.UID()
        return "%s/lookupObject?uid=%s" % (self.absolute_url(), uid)

We can use the method `lookupObject(uid)` to get the actual object by
UID, or use `reference_url(object)` to generate a "safe" URL to an
object that will always find it given its UID.

You can see the list of currently-tracked UIDs and actual objects in
the `archetype_tool`, `UID` tab.


Parent UID
----------

The Parent UID field created in our table is the UID of the container,
if it is an Archetypes object (or some other kind of future object
that might expose a UID).

This is **very** helpful for creating a simple parent/child
relationship in Plone, as we'll see in the next section.


Customers and Orders
====================

For example, a common database example is a database of customers and
orders, where one customer can have several orders. Pseudo-SQL for
this would be::

  CREATE TABLE Customer
    ( custid SERIAL NOT NULL PRIMARY KEY
    , custname TEXT
    ... other customer fields ...
    );

  CREATE TABLE Orders
    ( orderid SERIAL NOT NULL PRIMARY KEY
    , custid INT REFERENCES Customer
    ... other order fields ...
    );

The field `custid` in the `orders` table is a reference (called a
`foreign key`) to the field `custid` in the `customer` table.

To create a similar structure in Archetypes, we need to create just
two types: `CustomerFolder` and `Orders`.  Objects of both of these
types will get UIDs from Archetypes. But if we change our `Customer`
type to become folderish (ie, derived from Archetypes's `BaseFolder`
rather than `BaseContent`), it can contain objects, and we can add
`Orders` objects inside of it. These `Orders` objects will have their
Parent UID field set to the `CustomerFolder` UID, giving us an easy
way to write ZCatalog queries for all orders with a certain customer
UID, or SQL queries asking the same thing.


.. sidebar:: Why *Orders* Rather Than *Order?*

  *Order* is a reserved word in most relational databases (part of the
  clause `ORDER BY ...`) and therefore, many databases can't use it as
  a table name or field name without quoting it. At this time,
  Archetypes does not properly quote table and field names, and
  therefore, we can't use reserved words.

  Unless this is changed in Archetypes, when designing your schema, it
  would be wise to look at your database's list of reserved words and
  avoid these.


Creating in Archetypes
----------------------

Let's create these two new archetypes. First, the CustomerFolder. This
will be exactly the same as CustomerSQL, except using BaseFolder
rather than BaseContent::

  # CustomerFolder.py
  # Customer portal type (SQL storage, folderish)

  from Products.Archetypes.public import *
  from Products.Archetypes.TemplateMixin import TemplateMixin
  from Products.Archetypes.SQLStorage import PostgreSQLStorage

  schema = BaseSchema + Schema((
      
      TextField('body',
                required=1,
                primary=1,
                searchable=1,
                storage=PostgreSQLStorage(),
                default_output_type='text/html',
                allowable_content_types=('text/restructured',
                                         'text/plain',
                                         'text/html',
                                         'application/msword'),
                widget=RichWidget,
                ),
      
      StringField("phone",
                  storage=PostgreSQLStorage(),
                  index="FieldIndex",
                  ),
      
      )) + TemplateMixin.schema

  class CustomerFolder(TemplateMixin, BaseFolder):
      """Our example object"""
      schema = schema
      archetype_name = "Customer Folder"
      actions = TemplateMixin.actions
                    
  registerType(CustomerFolder)

Our Order type is straightforward. It will include the cost of an
order, and shipping details::


  # Orders.py

  from Products.Archetypes.public import *
  from Products.Archetypes.TemplateMixin import TemplateMixin
  from Products.Archetypes.SQLStorage import PostgreSQLStorage

  schema = BaseSchema + Schema((
      
      TextField('shipping_details',
                required=1,
                storage=PostgreSQLStorage()),
      FixedPointField('total_cost',
                      storage=PostgreSQLStorage())
      
      )) + TemplateMixin.schema

  class Orders(TemplateMixin, BaseContent):
      """Our example object"""
      schema = schema
      archetype_name = "Orders"
      actions = TemplateMixin.actions
                    
  registerType(Orders)


Testing Them Out
----------------

Register these two new types with portal_types and add a
`CustomerFolder` object. You should be able to edit this data and see
the resulting information in the table customerfolder without a
problem.

As of the writing of this HOWTO, Archetypes does not expose a "folder
contents" tab for folderish objects like our `CustomerFolder`.
However, you can go to this view manually by visiting the new customer
folder object, and changing the end of the URL to point to
`folder_contents`. [#]_

.. [#] And you can add this action to the type so that it
   automatically shows as a tab up by adding it to the actions for
   `CustomerFolder` in `portal_type`.

Inside of the new customer folder, add an `Orders` object and enter
details.  Then, examine the `orders` table in the database:

.. parsed-literal::

  database=# **SELECT \* FROM Orders;**
            uid           |           parentuid            | shipping_details | total_cost
  ------------------------+--------------------------------+------------------+------------
   Orders.2003-07-23.4935 | CustomerFolder.2003-07-23.4609 | Shipping         |          0
  (1 rows)

Notice how we get the `parentuid` value correctly. From our relational
database, we could write a traditional query now on customers and the
total of the orders as::

  database=# SELECT C.uid, C.phone, SUM(O.total_cost)
               FROM CustomerFolder as C
                 INNER JOIN Orders as O on (O.parentuid = C.uid)
               GROUP BY C.uid, C.phone;


Working With Existing Table Structure
=====================================

Of course, if you're working with existing tables, or if you want to
work with other SQL tools, chances are you want to use a more
traditional primary key/foreign key setup than the Archetypes UID.
Many databases use a serial column [#]_ (integers that increase for
each new record) as a primary key.

.. [#] MySQL uses an integer columns with the autoincrement feature.

To do this with Archetypes, you can simply either:

- create the table before you insert the first Archetypes record

or

- modify the table after Archetypes creates it and starts using it.

For example, our `customerfolder` table was created automatically by
Archetypes, and it contains a `UID` field, but not a traditional,
numeric primary key. We can fix this by adding this::

  ALTER TABLE Customerfolder ADD customerid INT;

  CREATE SEQUENCE customerfolder_customerid_seq;

  UPDATE Customerfolder SET customerid = nextval('customerfolder_customerid_seq');

  ALTER TABLE Customerfolder ALTER customerid
    SET DEFAULT nextval('customerfolder_customerid_seq');

  ALTER TABLE Customerfolder ALTER customerid SET NOT NULL;

  ALTER TABLE Customerfolder DROP CONSTRAINT customerfolder_pkey;
  
  ALTER TABLE Customerfolder ADD PRIMARY KEY ( customerid );

  ALTER TABLE Customerfolder ADD UNIQUE ( uid );

Note that syntax for altering tables, adding primary keys, etc.,
varies considerably from one relational database to another, so if
you're not using PostgreSQL, you'll want to research how to do this
with your relational database. Also note that it's rather wordy to
make this changes, whereas having the table setup properly in the
first place is much more succinct::

  CREATE TABLE Customerfolder ( customerid SERIAL NOT NULL PRIMARY KEY,
                                ...
                              )

So it may often be to your advantage to create the table before
Archetypes.

Now we have a traditional primary key that is automatically increased,
but since its not part of Archetypes's schema, it will leave it alone.

.. important::

  Notice that we make the UID field `UNIQUE`. This guarantees that two
  records cannot have the same UID. Even though we're no longer using
  the Archetypes UID as our primary key, it is still critical to keep
  this field unique.

  When Archetypes edits an object, it doesn't know if the object
  exists in the relational database yet or not. Therefore, it tries to
  insert a record for this object. If this fails, it then updates the
  existing record.

  This behavior may change in future versions of Archetypes, but,
  unless it does, you must make sure UID stays unique or else you'll
  have multiple copies of your objects' data in the relational
  database, only one of which will be correct.



If You Need A Very Different Table Structure
--------------------------------------------

Instead of having Archetypes write to the real table, we can have
Archetypes insert to a `view` of the table. Such a view can have
fields that looks like those that Archetypes expects, but actually
insert the information in different places and different ways.

This is especially useful if you have existing relational database
tables that have non-Zope-like fields, names, etc.

To do this, let's first move the real table out of the way::

  ALTER TABLE customerfolder RENAME TO customerfolder_table;

This is because Archetypes expects to work with `customerfolder`, and
we want that to be our view. The actual table name doesn't have to be
`customerfolder_table`; it can be whatever we want it to be.

Now, let's create our view::

  CREATE VIEW customerfolder AS
    SELECT uid, parentuid, body, phone
      FROM customerfolder_table;

Now, we'll make this view updatable so that new records can be
inserted into it. The syntax for this is very relational
database-specific; you'll need to change this for other database
systems. Following is our PostgreSQL syntax::

  CREATE RULE customerfolder_ins AS
    ON UPDATE TO customerfolder DO INSTEAD (
      INSERT INTO customerfolder_table ( uid, parentuid, body, phone )
        VALUES ( NEW.uid, NEW.parentuid, NEW.body, NEW.phone ); );

Now, Archetypes can insert to customerfolder, assuming that it is a
table, when in fact, we're *rewriting* its work to write to the real
table.

So that Archetypes can do updates and deletes, we'll need to add rules
for that, too::

  CREATE RULE customerfolder_del AS
    ON DELETE TO customerfolder DO INSTEAD
      DELETE FROM customerfolder_table WHERE uid=OLD.uid;

  CREATE RULE customerfolder_upd AS
    ON UPDATE TO customerfolder DO INSTEAD
      UPDATE customerfolder_table
        SET parentuid = NEW.parentuid
          , body = NEW.body
          , phone = NEW.phone;
          
In this example, our real table and view are only slightly different,
but this strategy is helpful when dealing with existing tables that
have many fields not of interest to Archetypes, or when our relational
database tables have a different type of structure than is natural to
Archetypes. We'll see advanced uses of this later.

FIXME: Show It Working



Using Traditional Referential Integrity For the Child Table
-----------------------------------------------------------

For our `orders` table, we can do the same thing to give that a
serial-type primary key that is more traditinal for a relational
database. In addition, though, it's likely that we want to child
orders table to relate to the parent `customerfolder` table by the new
`customerid` rather than the Archetypes-oriented Parent UID.

To do this, let's create a `customerid` field to the `order` table::

  ALTER TABLE Orders ADD customerid INT;

  UPDATE orders 
    SET customerid = Customerfolder.customerid
    FROM Customerfolder
    WHERE Orders.parentuid = Customerfolder.uid;

  ALTER TABLE Orders ALTER customerid SET NOT NULL;

  ALTER TABLE Orders ADD FOREIGN KEY (customerid) 
    REFERENCES Customerfolder;

Now we have a traditional primary key/foreign key relationship between
our tables. If we have a orders record for customer #1, we won't be
able to delete this customer until we delete these orders.

We need to set it up so that when we add an order via Plone, we look
up the `customerid` from the `customerfolder` table and set it in the
`orders` table for the new record.

To do this, we'll add a trigger that, before completing an insert on
the `order` table, figures out the `customerid` and makes that part of
the insert.

Different database implement triggers in different ways. In
PostgreSQL, a trigger statement is a simple statement that calls a
function. This function can reference and change a record structure
called `new` which reflects the new record being inserted (or for an
update, the new record to be written). Functions in PostgreSQL can be
written in different languages, including Python; for our example,
however, we'll use PostgreSQL's built-in PL/PgSQL language, a
PL/SQL-like language that is simple to write and understand.

Before you can write PL/PgSQL functions, you must enable this by
adding this language to your database. From the shell:

.. parsed-literal::

  $ **createlang plpgsql your_db_name**

Our trigger function will be::

  CREATE OR REPLACE FUNCTION order_ins () RETURNS TRIGGER AS '
    BEGIN
    NEW.customerid := customerid 
                        FROM customerfolder AS C
                        WHERE NEW.parentuid = C.uid;
    RETURN NEW;
    END;
  ' LANGUAGE plpgsql;

Now, let's create the trigger::

  CREATE trigger order_ins_trig BEFORE INSERT ON Orders
    FOR EACH ROW EXECUTE order_ins();

Our real test is whether this works in Plone, but for a Q&D
simulation, we'll test this in the SQL monitor by manually inserting a
child `orders` record and seeing if it gets the parent UID (for your
tests, use the real UID of one of your `CustomerFolder` objects):

.. parsed-literal::

  database=# **insert into orders (uid,parentuid)**
               **values ('test', 'CustomerFolder.2003-07-23.4609');**
  INSERT 35162 1
  database=# **select uid, parentuid, customerid from orders;**
            uid           |           parentuid            | customerid
  ------------------------+--------------------------------+------------
   Orders.2003-07-23.4935 | CustomerFolder.2003-07-23.4609 |          1
   test                   | CustomerFolder.2003-07-23.4609 |          1
  (2 rows)

In the above output, the second record is our newly inserted record,
and it did get the correct `customerid` field.


Referential Integrity & Prevention of Deletions
-----------------------------------------------

Now our traditional referenial integrity is set up. If we try to
delete a customer that has related orders, we'll get the error that we
expect and want:

.. parsed-literal::

  database=# **DELETE FROM Customerfolder;**
  ERROR:  $1 referential integrity violation - key in customerfolder still referenced from orders

However, we can still have problems in Plone.

Our current example has the child order objects nested inside of the
parent customer objects, so it's not possible to delete a customer
without deleting the orders because the customer itself is a folderish
object, so the orders would be deleted automatically.

However, this may not always be the setup. Sometimes, you won't be
able to have a child object contained physically in the parent object,
and you'll connect things using attributes yourself.

For example, we might want to keep track of which staff member handles
this customer. We could do this by nesting the `CustomerFolder`
objects inside a `Staff` object, but this might, for different
reasons, not be possible or preferable. Instead, we would create a
`staffuid` attribute on the `CustomerFolder` type, and populate this
with the UID of the staff member.

In cases like this, if you have the referential integrity in the
database connected properly, you won't be able to delete the staff
record if related customers exist, but you will be able to delete the
customer *object* in the ZODB without problems--stranding the data in
the relational database and ruining your database connections.

This is because the current version of Archetypes doesn't deal
properly with deletion exceptions. Archetypes issues an SQL delete on
the staff record, but since there are related children, it fails. This
raises an exception, but Zope only stops a deletion by raising and
propagating a particular exception--others just get logged and
ignored. Therefore, the database record can't be deleted (your
database will refuse to do this, regardless of how Zope asks), but the
pointer to it in the ZODB will be deleted. So the staff member won't
be visible on the site, but the data will stay in the relational
database.

To fix this, apply the patch FIXME included with this howto. This
raises the proper exception (`BeforeDeleteException`) if the SQL
deletion call fails, which causes the Plone object deletion to fail.
Unfortunately, you'll get an standard error message, rather than a
polite, user-friendly explanation, but this is better than silently
ignoring the database failure and moving on. [#]_

This patch was developed for the current version of Archetypes. This
fix may be included by the time you read this HOWTO. If so, please let
me know, and I'll update this section.

.. [#] If you want to make a nicer deletion error message, you could
   modify the `standard_error_message` method.


Cascading
+++++++++

PostgreSQL and most other databases that support referential integrity
can handle deletion of parent records in other ways. The default is to
block the deletion of parent with related children, but you can also
opt to automatically delete the children when a related parent is
deleted.

This option is called "cascading" a deletion. To set this up, we'd
create our child table differently:

.. parsed-literal::

  CREATE TABLE Child (
    childid SERIAL NOT NULL PRIMARY KEY,
    parentid INT NOT NULL REFERENCES Parent *ON DELETE CASCADE*
    ...
  );

Now, when the parent is deleted in the database, it will delete the
related child records rather than raising an exception.

Of course, this won't automatically delete the Zope ZODB objects for
the children, but the next section of this tutorial deals with the
question of how to have operations in the database "notify" Zope of
changes to make in the ZODB. Using techniques explained there, we'll
be able to have the child ZODB deleted for us.


Propagating Direct DB Changes Back to ZODB
==========================================

Sometimes in Zope projects, the changes all come from the Zope
interface, and the relational DB storage is just to soothe
ZODB-nervous customers, or to allow reporting from standard SQL tools.
In this case, the setup we have would be acceptable.

In cases where changes must propigate to Zope, here are some problems
we need to solve:

- Records that are inserted directly into the database are never
  visible to Zope, as ZODB objects aren't instantiated for these
  records.

- Records that are deleted directly in the database are never deleted
  from Zope. Therefore, objects will remain in the ZODB that point to
  records that are no longer in the relational database. The current
  version of Archetypes raises an error if you try to view these
  objects or get the attributes that are stored in SQLStorage.

- Records that are changed in the database **are** visible immediately
  to Zope, but any Catalog entries won't be updated, making Catalog
  queries incorrect.


Forcing Catalog Reindexes on Update
-----------------------------------

There's no way for our relational database to directly affect the
ZODB.  Instead, we'd have to either make a request that the ZServer
hears and passes on to Plone, or we'd have to write a standalone
Python program that connects to the ZODB to make these requests. [#]_

.. [#] An advanced note on a future possibility: It should be possible
   to have PL/PythonU, PostgreSQL's untrusted procedural language
   binding for Python, import the Zope module and work directly with
   Zope objects. However, when I tried this with Zope 2.7.0b1 and
   PostgreSQL 7.4devel (the first version of PostgreSQL to support
   PL/PythonU), it hung my PostgreSQL process. If this becomes
   possible with other configurations, we'll be able to not use the
   `wget`-based strategy outlined below, and talk directly to Zope.

The latter can be very slow (starting connecting to the ZODB can take
a while), and would only work on the machine that the ZODB is hosted
on, whereas the first choice is ZEO-friendly, remote database machine
friendly, and generally easier and faster.

By creating a custom function in PostgreSQL, we can execute a web or
XMLRPC request to reindex the catalog.

We'll need a bit of Zope support: Zope will be given the UID for the
record that has changed, and it needs to find the real Zope object,
and call `reindexObject()` on it.

We could do this by adding a method to `ArchetypesTool.py` [#]_, but,
for simplicity's sake, we'll implement it as a PythonScript::

  # "reindex_by_uid"

  ## Parameters: uid

  o = context.archetype_tool.lookupObject(uid)
  o.reindexObject()
  return "ok"

You can test calling this by giving it a UID of an existing object.
This should be recataloged; you can see the changed catalog
information by viewing the `portal_catalog`.

.. [#] I think it would be a good idea to move helper methods like
   this into the Archetypes API. We'll see what happens.
   
Functions can be written in several procedural languages in
PostgreSQL, including Python.  However, making a web request is an
"unsafe" act in PostgreSQL, so we need to use a language that supports
making unsafe calls.  PostgreSQL refers to these languages as
"untrusted" languages, and traditionally names them with a trailing
*U*. At this time, the Python language is implemented as a trusted
language but not as an untrusted language. The built in, easy-to-use
PL/PgSQL is also implemented as a trusted language only.

This is changing, howver, in PostgreSQL 7.4. Due to `RExec`
(restricted environment) module being dropped from Python, PL/Python
(trusted) is no longer part of PostgreSQL, and PL/PythonU (a new,
untrusted variant) is being added. It would be easy to write the
functions below as PL/PythonU functions. [#]_ 

Our current options for untrusted languages, though, are PL/tclU (tcl
untrusted), PL/perlU (perl untrusted), and C. We'll use Perl's
untrusted language, plperlu.

.. [#] In earlier versions of PostgreSQL, you could use PL/Python
   (trusted) by recompiling PL/Python after adding the
   required-for-import modules to the list of acceptable modules.
   However, you'd have to install this modified PL/Python library on
   every PostgreSQL server that was going to use these functions.

Make sure that Perl untrusted functions are enabled for your database:

.. parsed-literal::

  $ **createlang plperlu your_db_name**

Then, in psql, we'll create a function that uses `wget`, a common,
simple command line http request tool::

  CREATE OR REPLACE FUNCTION reindex_by_uid (text) RETURNS text as '
    $uid = shift;

    # Auth required to run PythonScript w/right role
    #    or, dont pass auth stuff and make PyScript proxied to role
    $AUTH = "--http-user=joel --http-passwd=foo";

    # Set to your server and portal name
    $SERVER = "http://localhost:8080/arch";

    # wget options
    #   -q     is quiet (no status output)
    #   -O -   is to send results to standard output
    #   -T 5   is to timeout after 5 seconds
    $WGET = "/usr/bin/wget -q -O - -T 5";

    $cmd = "$WGET $AUTH $SERVER/reindex_by_uid?uid=$uid";

    # output it to psql log so the user has some idea whats going on
    elog NOTICE, $cmd;

    return `$cmd`;
  ' LANGUAGE plperlu;

As noted in the function comments, above, you can pass authorization
headers via wget (using the $AUTH variable). If you don't want to have
the username and password in a plaintext script on the PostgreSQL
server, or don't want them to travel across the network, you could
instead make the PythonScript usable by anonymous users, and have it
proxied to a high-enough level role that it can reindex all needed
content.

The `elog` statement in the function outputs the `$cmd` variable
through the PostgreSQL logging system, making it appear in `psql` as a
notice. This is useful for debugging and providing feedback, but may
confuse some database front-end systems that don't expect notices to
be raised. In addition, it exposes your username and password to the
log everytime a record is updated. Once you have the function working
for your database, you should probably remove this line.

Now, in PostgreSQL, if we update a record, we can force a reindex by
calling this, as in:

.. parsed-literal::

  database =# **SELECT reindex_by_uid('*uid*');**


Using Triggers to Automate This
+++++++++++++++++++++++++++++++

Of course, we'll want to have this happen automatically when we update
a record, rather than having to execute the select statement.  To do
this, we'll write a trigger in PostgreSQL that triggers whenever an
update is made to our customer table.

To do this, we need a trigger function that is called when our table
is changed. In a perfect world, we could use our Perl function, above.
However, at this time, Perl functions can't be used as trigger
functions (though functions written in PL/Python, PL/PgSQL, C, PL/tcl,
and other procedural languages can). For a simple wrapper function
like this, PL/PgSQL would be the normal choice.

Our trigger function is::

  CREATE OR REPLACE FUNCTION customer_upd() RETURNS TRIGGER as '
    BEGIN
      PERFORM reindex_by_uid(OLD.uid);
      RETURN NEW;
      END;
  ' LANGUAGE plpgsql;

Then the trigger itself::

  CREATE TRIGGER customer_upd 
    AFTER UPDATE ON Customerfolder
      FOR EACH ROW EXECUTE PROCEDURE customer_upd();

Now, whenever we make an change to our table, our trigger calls the
PL/PgSQL function customer_upd. This, in turn, calls our general
reindexing function, which makes a simple web request that Zope hears
and calls the reindexing support PythonScript. It seems like a lot of
redirection, but works fine. Go test it out. Make a change to your
object's body field directly via PostgreSQL, then check the catalog
results and see that the appropriate field (in this case,
SearchableText) has been updated.


Syncronizing Deletes and Inserts
--------------------------------

*(For advanced readers, since some of the detail is left to you to
fill in).*

Deletes and inserts are a bit trickier than updates, but also more
critical to get right. If you don't use the update/reindexing
technique, above, everything works fine, except your ZCatalog calls
will be out-of-date, and even those will be fixed for you the next
time you edit the object in Plone or do a manual recataloging. If
inserts and deletes aren't propagated from the relational database to
ZODB, data will be missing and errors will be raised.

For this reason, it may be reasonable to decide that record additions
and deletions should happen only via the Plone interface. You can make
quick data changes in the relational database (helpful for fixing
typos across a series of records, or reformatting a field, etc.), but
never inserts or updates.

However, if you want or need to have insertions/deletions made to the
relational database and propagated into the ZODB, the following
sections explain how to do this.


Inserts
+++++++

Inserts would be handled using the saem general concepts as the
update/reindex fix: write a Zope PythonScript that creates the object
when it is passed the different fields required for object creation.
Then write a PL/perlU function that crafts a command line `wget`
statement that calls our Zope PythonScript, all of this being set into
motion by a trigger on our table.

First, we'll want to create a PythonScript that will create our
content for us. The trickiest part is coming up with a good, unique
UID. If we knew that something in our table that was being inserted
was unique, we could use that (prepended by the type name, to make
sure it was unique across types so that Archetypes could use it).
However, to look and feel consistent with UIDs created through the
web, we'll copy in the same UID-generating code that Plone itself
uses. [#]_

.. [#] It would be smarter, of course, to simply call an API method to
   get a unique ID in this format, but I couldn't find a suitable way
   to do so given how this has been implemented. If any readers have a
   suggestion, please let me know.

Our script will be called `create_customerfolder`, and will be::

  ## create_customerfolder
  ## Arguments: phone, body

  # this function ripped out of CMFPlone/FactoryTool.py
  def generateId(self, type):
      now = DateTime()
      name = type.replace(' ', '')+'.'+now.strftime('%Y-%m-%d')+'.'+now.strftime('%H%M%S')

      # Reduce chances of an id collision (there is a very small chance that somebody will
      # create another object during this loop)
      base_name = name
      objectIds = self.getParentNode().objectIds()
      i = 1
      while name in objectIds:
          name = base_name + "-" + str(i)
          i = i + 1
      return name

  context.invokeFactory( "CustomerFolder"
                       , id=generateId(context, 'CustomerFolder')
                       , phone=phone
                       , body=body)
  return "ok"

You can test this script by calling it through the web, or by using
the `Test` tab on the PythonScript. Give it a `body` and a `phone` and
it will create a new `CustomerFolder` object in the current context.

Now, we'll write a plperlu function that will craft a proper `wget`
web request to call this script::

  CREATE OR REPLACE FUNCTION customerfolder_add (text,text) RETURNS text as '
    $body = shift;
    $phone = shift;
    $sec = "--http-user=joel --http-passwd=foo";
    $portal = "/arch";
    $server = "localhost:8080";
    $wget = "/usr/bin/wget";
    $cmd = "$wget $sec -q -O - http://$server/$portal/create_customer?body=$body".''\\\&''."phone=$phone";
    return `$cmd`;
  ' LANGUAGE plperlu;

FIXME -- CLEAN THIS UP LIKE PREVIOUS

The difference is that we don't want to really do an insert in the
database, though--when Zope does its object creation, it will create
the database record itself in Archetypes. So we want our original
direct-in-DB insert to be ignored.

We could do this with a trigger, and have the trigger raise a failure
so the insert didn't happen. This, though, would be confusing for the
user, who would see an error message, and, if we were in the middle of
transaction, would spoil that transaction, aborting it and preventing
other actions from happening in the relational database. A better
solution, then, would be to use a feature of PostgreSQL called
`rules`, which we saw briefly earlier `If You Need A Very Different
Table Structure`_.

Rules are rewritings of a query to do anything instead of the
called-for-query. We'll "rewrite" our `INSERT` query to a `SELECT`
query, which in this case will select the PL/perlU function that
calls `wget` to notify the Zope PythonScript to create the object.
Again, it seems like a lot of redirection, but works well.

Rule creation is covered in the PostgreSQL documentation, in `The Rule
System`_. Our rule will be::

  CREATE RULE customer_ins AS 
    ON INSERT TO Customerfolder 
    WHERE NEW.uid = 'direct'
    DO INSTEAD 
      SELECT customerfolder_add ( NEW.body, NEW.phone );

Now, when you want to insert a record directly, you can do so by::

  INSERT INTO customer_ins ( uid, body, phone ) 
    VALUES ( 'direct', 'body goes here', '555 1212' );

The `WHERE NEW.uid = 'direct'` clause is required to prevent Zope's
insertion from triggering our rule which would trigger Zope's
insertion ... and so on into permanent recursion. Any attempt to
insert a record with a `UID` not equal to "direct" will go directly
into the database without triggering any action from Zope. Since Zope
will be inserting a record with real UID, it will always therefore
bypass our rule.

.. _`The Rule System`: http://www.postgresql.org/docs/7.3/static/rules.html

Deletes
+++++++

Deletes would be handled like inserts, but our PythonScript would
obviously do the deleting for us instead.

Details here can be figured here by the reader, but you'll need a
PythonScript to handle the deletion, a plperlu function to craft the
proper `wget` command, and a trigger that handles `ON DELETE`.

Since we can't stop recursion from happening with a DELETE the way we
can with an INSERT, we should have our trigger call Zope not just as
`DO INSTEAD` but `DO`, so the Zope deletion happens and the normal
PostgreSQL deletion happens.  When the Zope deletion tries ...


Inserting a Child Record
++++++++++++++++++++++++

If we want to allow direct database insertion of the child `Orders`
objects, we have to consider one additional wrinkle: the `Orders`
objects are meant to be physically contained in their related parent
`Customer` object. Therefore, our PythonScript that would add their
child `Orders` record must make the context for the `invokeFactory`
call be the context of the enclosing `Customer` object.

We could accomplish this easily by passing the child `Orders`
PythonScript add helper the `UID` of the `Customer`, and it could
lookup the `Customer` object (using the API demonstrated earlier for
looking up an object given its UID). Then we could use that context
for our `invokeFactory` call.

FIXME: show this.


Changing SQLStorage's Storage Methods: An Example With Lists
============================================================

Creating the Types and Fixing the Mapping
-----------------------------------------

If we add a list type to our customer object, we run into a snag with
marshalling and unmarshalling.

Let's add the object type, first as a standard Archetypes object
stored completely in the ZODB::

  # CustomerList.py

  from Products.Archetypes.public import *
  from Products.Archetypes.TemplateMixin import TemplateMixin

  schema = BaseSchema + Schema((
      
      TextField('body',
                required=1,
                primary=1,
                searchable=1,
                default_output_type='text/html',
                allowable_content_types=('text/restructured',
                                         'text/plain',
                                         'text/html',
                                         'application/msword'),
                widget=RichWidget,
                ),
      
      StringField("phone",
                   index="FieldIndex",
                   ),
      LinesField("clients"),
      
      )) + TemplateMixin.schema

  class CustomerList(TemplateMixin, BaseContent):
      """Our example object"""
      schema = schema
      archetype_name = "Customer List"
      actions = TemplateMixin.actions
                    
  registerType(CustomerList)

Put this in the schema and restart Archetypes.

As we're storing this in the ZODB (not in the relational database),
everything works fine. The form widget for the clients field is a
textarea in which the user enters newline-separated entries. These are
converted by Zope to a Python list and stored as an attribute of the
object.

If we create a new Archetypes type that contains this same lines
field, but tries to store it in the relational database, we run into
problems with Archetypes's default behaviors.

First, the object type::

  # CustomerListSQL.py

  from Products.Archetypes.public import *
  from Products.Archetypes.TemplateMixin import TemplateMixin
  from Products.Archetypes.SQLStorage import PostgreSQLStorage

  schema = BaseSchema + Schema((
      
      TextField('body',
                required=1,
                storage=PostgreSQLStorage(),
                primary=1,
                searchable=1,
                default_output_type='text/html',
                allowable_content_types=('text/restructured',
                                         'text/plain',
                                         'text/html',
                                         'application/msword'),
                widget=RichWidget,
                ),
      
      StringField("phone",
                   index="FieldIndex",
                   storage=PostgreSQLStorage(),
                   ),
      LinesField("clients",
                storage=PostgreSQLStorage()),
      
      )) + TemplateMixin.schema

  class CustomerListSQL(TemplateMixin, BaseContent):
      """Our example object"""
      schema = schema
      archetype_name = "Customer List SQL"
      actions = TemplateMixin.actions
                    
  registerType(CustomerListSQL)

Restart Archetypes, and don't forget to add the new type to
`portal_types`.

At the time of this writing, Archetypes tries to create the new table
with the field type `lines` for the `clients` field. This is not a
valid field type for PostgreSQL (or any other database I know of), and
therefore, the addition of the table fails, and any attempt to add an
object of this type fails since there is no table to store them in.

There are several different ways we could fix this problem.

- **Create the table before Archetypes does.** 

  If the table already exists, Archetypes won't create it. We can
  easily create the table, and give it a `text` type for the `clients`
  field.

  The table structure would be::

	  CREATE TABLE Customerlistsql (
	      uid text NOT NULL PRIMARY KEY,
	      parentuid text,
	      body text,
	      phone text,
	      clients text
	  );

- **Change the mapping performed by Archetypes.**

  We can fix this problem by patching `SQLStorage.py` to do the right
  thing and create a `text` field by changing the type mapping that
  Archetypes does. You can do this either by editing `SQLStorage.py`
  and making changes for your database type, or, if you'd rather not
  modify the Archetypes source code, you can subclass your storage
  type, make the changes there, and use this new subclassed storage
  type. We'll look explicitly at the subclassing strategy later in
  this document; for now, we'll make changes directly to
  `SQLStorage.py`.

  The change we want is in the dictionary `db_type_map`, which
  translates an Archetypes field type into the relational database
  field type. As of this writing, there is no translation for `lines`,
  so Archetypes uses `lines` as the relational database field type.
  We'll add a translation for `lines` to become `text`::

      db_type_map = {
	  'object': 'bytea',
	  'file': 'bytea',
	  'fixedpoint': 'integer',
	  'reference': 'text',
	  'datetime': 'timestamp',
	  'string': 'text',
	  'metadata': 'text', 
	  'lines':'text', # THIS IS THE CHANGE
	  }

  If you restart Archetypes and try to add your object now, it will
  create the table and let you create objects.

- **Create a suitable domain in PostgreSQL.**

  PostgreSQL, like many advanced SQL databases, supports the notion of
  *domains*. A domain is a custom-defined explanation of a database
  type, which can be referenced as if it were a real type.

  For example, if you commonly want to use a `varchar(20) not null`
  for telephones in a database, you could create a domain called
  `telephone` that is defined as `varchar(20) not null`, and then you
  can simply create your tables with the field type `telephone` to get
  the right definition and behavior.

  We'll create a domain called `lines`::

    CREATE DOMAIN lines AS text;

  Domains can contain restrictions (such as `CHECK` constraints and
  `NOT NULL` requirements), but in this case, we don't want or need
  any of these. This simple definition will be enough.

  Now, when Archetypes tries to create a field with the type `lines`,
  it will succeed.

  In some ways, this is the best strategy of our three, as it lets
  other applications and users understand that this is a `lines`
  field. It's still stored as `text`, and behaves as such, but if you
  look at the table structure, you'll see `lines`, which can remind
  you of its newline-separated, list-oriented use.

  
Fixing the Translations
-----------------------

A serious problem still persists, though.

The newline-separated entries from the form (the "lines") are turned
into a Python list by Archetypes, such as::

  [ 'cat', 'dog', 'bird' ]

but SQLStorage attempts to store this list **directly** in the
database. This ends up as the literal string value
"['cat,'dog','bird']" which is Archetypes stores in the database::

  database=# SELECT uid, clients FROM Customerlistsql ;
                 uid               |        clients
  ---------------------------------+------------------------
   CustomerListSQL.2003-07-23.1619 | ['cat', 'dog', 'bird']
  (1 row)


Unfortunately, this string representation of a Python list is a
difficult format to work with in the database, and not handled
correctly coming out by Archetypes. When Archetypes gets the data back
from the relational database, it sees it as a single string. It tries
to turn this isnto a list, with the following results::

  [
  '
  c
  a
  t
  '
  ,

  '
  d
  o
  g
  '
  ,

  '
  b
  i
  r
  d
  '
  ]
 
As this is the way Python handles being given a string and being told
to treat it like a list.

The solution is that we want to write a custom marshaller and
unmarshaller.  These are the routines that Archetypes will run on a
value before it tries to write them to the database, and after it
retrieves the value from the database.

There are hooks in Archetypes for this: any function called map_*
is called when storing field type * and a method called
unmap_* is called when retrieving field type *.

Our mapping will convert this list back to a newline-separated string,
and this is the format it will be given to our relational database
as::

    def map_lines(self, field, value):
        return '\n'.join(value)

Our unmapping method will convert the newline-separated string back to
a Python list::

    def unmap_lines(self, field, value):
        return value.split('\n')

Both of these should go into `SQLStorage.py`, as methods the class
`SQLStorage` or as methods of the class for your particular relational
database.  If don't want to (or can't) modify the source to
Archetypes, you could subclass your storage class, add the methods to
the subclass, and have your object schema fields use your new,
subclass storage type. We'll cover this concept of subclassing a
storage class extensively later, when we subclass an improved version
of the PostgreSQL storage class.

Now we can transparently work with our lists: they appear and are
edited on the form as a newline-separated string (so we can easily
edit them in a textarea), they're handled in Zope as a Python list
object (so we can work naturally with them and don't have to be
concerned with how they're stored), and they're stored in the
relational database as a simple newline separated list so we can
access them simply. [#]_

.. [#] Thought PostgreSQL doesn't have any problems arising here, you
   should ensure that there are no problems with your database
   converting newlines to another character or messing with the text
   fields in any way that will prevent our `unmap_lines` method from
   being able to retrieve the individual lines. If some kind of
   unhelpful conversion does occur, you should check to see what kind
   of binary storage your database offers, as binary storages perform
   no conversion at all in a relational database. PostgreSQL offers a
   binary storage type, `bytea`, but we don't need it in this case as
   it leaves the newlines alone.



Even Better: Turning Into Arrays
--------------------------------

While our solution above lets Archetypes store the data and get it
back in one piece, it isn't very suitable in the relational database:
most relational database querying programs and reporting programs are
ill-equipped to deal with searching for individual values that are
stuffed into text fields. 

To find all customers that have two values, "fish" and "cat", in
clients, you could write queries like::

  SELECT * FROM Customerlistsql
    WHERE clients LIKE 'cat\n%fish'
      OR clients LIKE 'cat\n%fish\n%'
      OR clients LIKE '%\ncat\n%fish'
      OR clients LIKE '%\ncat\n%fish\n%'
      OR clients LIKE 'fish\n%cat'
      OR clients LIKE 'fish\n%cat\n%'
      OR clients LIKE '%\nfish\n%cat'
      OR clients LIKE '%\nfish\n%cat\n%'

*(and this is still an incomplete example for this!)*

However, this is ugly, slow, unindexable [#]_, and error-prone,
especially as you add more predicates to the logic.

.. [#] Actually, in some databases, including PostgreSQL, there are
   ways to do a full-text index on a field like this, but this would
   still be suboptimal compared to more natural ways to store multiple
   values on a field.

We'll exploit a feature of PostgreSQL that allows us to store arrays
in a field, so that one field holds an array of values. While this is
similar to storing as newline-separated text, there are many functions
in PostgreSQL that can quickly find records having a value in an
array, or count the number of values in an array, and so on--all the
things that would be slow and unwieldy using text.

First, let's change our table structure to use arrays:

.. parsed-literal::

  database=# **ALTER TABLE Customerlistsql DROP CLIENTS;**
  ALTER TABLE

  database=# **ALTER TABLE Customerlistsql ADD CLIENTS text[];**
  ALTER TABLE

The type `text[]` is a PostgreSQL type for storing an array of text
values.  We can test out the array storage works directly in
PostgreSQL by updating an existing record and examining it:

.. parsed-literal::

  database=# **UPDATE Customerlistsql SET clients='{cat,dog,bird}';**
  UPDATE 1
  
  database=# **SELECT uid, clients FROM Customerlistsql;**
                 uid               |    clients
  ---------------------------------+----------------
   CustomerListSQL.2003-07-23.1619 | {cat,dog,bird}
  (1 row)

  database=# **SELECT uid, clients[1] FROM customerlistsql;**
                 uid               | clients
  ---------------------------------+---------
   CustomerListSQL.2003-07-23.1619 | cat

Now we can change our `map_lines` and `unmap_lines` methods from
above, to write out and retrieve values written in this format::

    def map_lines(self, field, value):
        return "{%s}" % ','.join(value)

    def unmap_lines(self, field, value):
        return value.strip("{}").split(',')

.. note::

  These are very naive implementations, as they do not deal with the
  possibility that a list item might have a comma in it. It would be
  quite easy, though, to write versions that quoted the comma and
  unquoted it for unmapping.

Restart Archetypes to pick up the changes to the storage type, then
edit an existing or add a new object. Notice how the values you put
into the `clients` field end up as array in PostgreSQL, and are read
correctly.


Turning lists into related child records
----------------------------------------

While the last section works wonderfully, not everyone is lucky enough
to work with PostgreSQL, "The World's Most Advanced Open Source
Database". Many databases don't support an array type.

In this case, or even when using PostgreSQL, you can store the
individual client items in a related child table. We could, of course,
do this entirely in stock Archetypes: have the `Customer` object be
folderish (inherited from `BaseFolder`), and add independent client
objects, as we did earlier for `Orders`. In some cases, as it did for
`Orders`, this makes sense: if the child record has more than one
piece of information to it, or if it might need to undergo separate
approval, workflow, etc., you want to have a customizable way for
Archetypes to let users edit this information, etc.

In many cases, though, this would be overkill and annoying for the
user. For keeping track of a simple list of names or such (as our
examples for the clients field have been), having to add separate
objects for each individual client is burdensome from a UI
perspective, and creates additional Zope objects that aren't really
needed.

Rather, we'll keep our simple, clean textarea/`lines` interface, but
dynamically create and delete child records in a related table as
needed.

We'll store these list items in a related table, called clients::

  CREATE TABLE clients ( uid TEXT NOT NULL
                       , client TEXT NOT NULL
                       , PRIMARY KEY ( uid, client ) );

.. note::

  (the last line in this statement makes the primary key a *compound
  primary key* composed of both the `uid` and `client` fields. We can
  have multiple children for each parent UID, and different parents
  can have the same client value, but each child can have the same
  client only once. If it should be possible in your application that
  the same item could appear in the list more than once, remove this
  restriction.)

What we now is a incoming function that will take the
newline-separated string and create child records for each line, and
an outgoing function that will turn child records back into a
newline-separated string.

So far, we've written procedural functions in PostgreSQL in both
PL/PgSQL and PL/perlU. We could do this new function in either of
those languages. PL/PgSQL has very poor string handling, though, so
we'll rule that out. Instead of coding more Perl (this is a Zope
HOWTO, after all!), let's take this chance to try out Python coding in
PostgreSQL. The examples below do not require any untrusted language
features, so they'll work with PL/Python (PostgreSQL 7.3 and previous)
or PL/PythonU (PostgreSQL 7.4); however, if you're using PL/PythonU,
you'll need to change the `LANGUAGE` declaration at the end of the
function definition to be `plpythonu`.

First, make sure that plpython is enabled for your database:

.. parsed-literal::

  $ **createdb plpython your_db_name**

Then, let's add a Python function that, given the `uid` and
newline-separated `clients` field, adds the child records::

  /* split newline-sep text and insert into child table */

  CREATE OR REPLACE FUNCTION lines_to_clients (text, text) RETURNS integer as '
     plan = plpy.prepare( "INSERT INTO Clients VALUES ( $1, $2 )", 
       [ "text", "text" ] )
     plpy.execute("DELETE FROM Clients WHERE uid=''%s''" % args[0])
     for ln in args[1].split("\\n"):
         plpy.execute(plan, [ args[0], ln ])
     return 1'
   LANGUAGE plpython;

First, we delete any existing clients associated with this `uid`.
Then, we iterate over the list, and inserts a client for each entry.
You can find out full information about using PL/Python with
PostgreSQL at `PL/Python`_.

.. _`PL/Python`: http://www.postgresql.org/docs/7.3/interactive/plpython.html

We can try out our function to make sure it works:

.. parsed-literal::

  database=# **SELECT lines_to_clients('a','one\\ntwo\\nthree');**
   lines_to_clients
  ------------------
                  1
  (1 row)

  database=# **SELECT \* FROM Clients;**
   uid | client
  -----+--------
   a   | one
   a   | two
   a   | three
  (3 rows)

You can ignore the return value of the first `SELECT`; functions must
return a value, so the one is just a throwaway value. The second
`SELECT`, however, demonstrates that our function is working.

Now, a function to pull together all of the children and return as a
newline-separated string::

    /* get child records and concatenate into newline-sep text */

    CREATE OR REPLACE FUNCTION clients_to_lines (text) RETURNS text as '
       rv = plpy.execute("SELECT client FROM Clients WHERE uid=''%s''" % args[0])
       return "\\n".join([ ln["client"] for ln in rv ])
    '
      LANGUAGE plpython;

And we can test that:

.. parsed-literal::

  database=# **select clients_to_lines('a');**
   clients_to_lines
  ------------------
   one
  three
  two
  (1 row)

We can see that our individual records are returned as one row of
newline-separated text. (There isn't actually a space at the start of
the "one" record; this is simply a mirage created by the formatting
`psql` does of query results).

To use this, though, we'll need for PostgreSQL to return the result of
`clients_to_lines` when Archetypes selects from the table--so we'll
need to use a view instead of our table. Views are discussed earlier
in this document, in `If You Need A Very Different Table Structure`_.
[#]_

.. [#] In some databases, you can change create fields that have
   values that are always calculated. If we were working with a
   database that had this capability, we wouldn't have to create a
   view; instead, we could define our `clients` column as calculated
   by `clients_to_lines()`.

First, we'll move the table to a new name::

  ALTER TABLE customerlistsql RENAME TO customerlistsql_table;

Then create our view::

  CREATE VIEW customerlistsql AS
  SELECT uid
       , parentuid
       , body
       , phone
       , clients_to_lines(uid) AS clients
    FROM customerlistsql_table;

Note that we explicitly tell our relational database to call the final
column in the view by the name `clients`. Otherwise, our relational
database wouldn't know what to call this field and would give it a
generic name, and Archetypes couldn't find it.

Next, we'll create the update rule. This is what will be called when
you try to update the view. It performs a normal update to the
behind-the-scenes `customerlistsql_table` table, then calls our
inserting function function for the clients::

  CREATE RULE customerlistsql_upd AS 
    ON UPDATE TO customerlistsql DO INSTEAD ( 
      UPDATE customerlistsql_table
         SET uid=NEW.uid
           , parentuid=NEW.parentuid
           , body=NEW.body
           , phone=NEW.phone
         WHERE uid=OLD.uid; 
      SELECT lines_to_clients(NEW.uid, NEW.clients); 
    );

We can test this out:

.. parsed-literal::

  database=# **UPDATE Customerlistsql SET clients='dog\\ncat';**
   lines_to_clients
  ------------------
                  1
  (1 row)

  database=# **SELECT uid, clients FROM Customerlistsql;**
                 uid               | clients
  ---------------------------------+---------
   CustomerListSQL.2003-07-23.1619 | cat
  dog
  (1 row)

Again, we can ignore the `SELECT` results we get from our `UPDATE`.
This is because our function is returning some information, even
though it's not useful to us. [#]_

.. [#] If you're really obsessive about such things, or you have other
   frontends to the database that throw a fit about receiving results
   back from an `INSERT` statement, this can be fixed. You could write
   the `INSERT` rule to just do the insert to the
   `customerlistsql_table` table, then add a trigger to that that
   table which calls our `lines_to_clients` function.  You'll have to
   change the `lines_to_cilents` function to work as a trigger
   function (it needs to return type `trigger` and such), but at the
   end of this process, you'll have an `INSERT` without any selecting
   results, which will trigger the desired child-insertion features.
   This is probably a step that most of us won't need, though.

Our insert rule is similar and straightforward::

  /* when inserting into the view, break apart the new mylines
     value and insert
  */

  CREATE RULE customerlistsql_ins AS 
    ON INSERT TO customerlistsql DO INSTEAD ( 
      INSERT INTO customerlistsql_table ( uid
                                    , parentuid
                                    , phone
                                    , body
                                    ) 
                                    VALUES ( NEW.uid
                                           , NEW.parentuid
                                           , NEW.phone
                                           , NEW.body
                                           ); 
      SELECT lines_to_clients( NEW.uid, NEW.clients ); 
    );
                  
We can test this in PostgreSQL to see that it works. First, our
insert::

  INSERT INTO customerlistsql ( uid
                              , parentuid
                              , phone
                              , body
                              , clients ) 
                              values ( 'b'
                                     , 'c'
                                     , '555-1212'
                                     , 'body'
                                     , 'one\ntwo\npickle\nshoe' );

Now, let's examine the results:

.. parsed-literal::

  database=# **SELECT \* FROM customerlistsql WHERE uid='b';**
   uid | parentuid | body |  phone   |       clients
  -----+-----------+------+----------+---------------------
   b   | c         | body | 555-1212 | one
  pickle
  shoe
  two
  (1 row)

  database=# **SELECT \* FROM clients WHERE uid='b';**
   uid | client
  -----+--------
   b   | one
   b   | pickle
   b   | shoe
   b   | two
  (4 rows)

.. note::

   In most relational databases (including PostgreSQL), there's no
   guarantee that the order records were inserted is the order they
   will be selected back out (that's what the `ORDER BY` clause of the
   `SELECT` statement is for.) In this last example, we inserted
   `one\\ntwo\\npickle\\nshoe` but got back the re-ordered `[one,
   pickle, shoe, two]`. If the order of items is important to your
   database application, see `Maintaining order`_ ,below.

And, finally, our `DELETE` rule::

  /* when deleting from the view, delete the child records as well */

  /* note: this could be handled automatically if we used referential
     integrity and has 'on delete cascade' in our table definition
     for the child table. 
  */

  CREATE RULE customerlistsql_del AS 
    ON DELETE TO customerlistsql DO INSTEAD ( 
      DELETE FROM clients 
        WHERE uid=old.uid; 
      DELETE FROM customerlistsql_table 
        WHERE uid=old.uid; 
    );

And we can test this last piece in PostgreSQL:

.. parsed-literal::

  database=# **DELETE FROM customerlistsql WHERE uid='b';**
  DELETE 1

  database=# **SELECT \* FROM customerlistsql WHERE uid='b';**
   uid | parentuid | body | phone | clients
  -----+-----------+------+-------+---------
  (0 rows)

  database=# **SELECT \* FROM clients WHERE uid='b';**
   uid | client
  -----+--------
  (0 rows)


Delete rule versus referential integrity
++++++++++++++++++++++++++++++++++++++++

As mentioned in the comments, the delete rule would not be neccessary
if you have referential integrity on the `customerlistsql` and
`clients` tables. In this case, you could either block deleting a
`CustomerListSQL` object if it had any related clients, or you could
cascade the deletion. Since this is a small, related table that is
meant to change everytime someone edits the `CustomerListSQL` object,
cascading seems more likely to be your choice.

We could set this up as::

  ALTER TABLE Clients ADD FOREIGN KEY (uid)
    REFERENCES customerlistsql_table ON DELETE CASCADE;

And drop our deletion rule and recreate it in a simpler form::

  DROP RULE customerlistsql_del ON customerlistsql;

  CREATE RULE customerlistsql_del AS
    ON DELETE TO customerlist_sql DO INSTEAD 
      DELETE FROM customerlistsql_table
        WHERE uid=OLD.uid;

Note that even though our deletion rule is as straightfoward as
possible, we still need it, since PostgreSQL (and most relational
databases) won't let you delete from a view unless you have a rule
explaining how to do it.

The referential integrity version is slightly nicer as it protects you
in case you deleted directly from `customerlistsql_table`.



Maintaining order
+++++++++++++++++

As we saw in the above section, the order of the child client lines as
retrieved may not match the order they were inserted.

We can solve this, if we need to, by adding a `SERIAL` field to our
`client` table and using this same field to order the selections.

Let's add the field to our table::

  CREATE SEQUENCE clients_sort_seq;

  ALTER TABLE clients ADD sort INT;

  UPDATE client SET sort = nextval('clients_sort_seq');

  ALTER TABLE clients ALTER sort SET NOT NULL;

  ALTER TABLE clients ALTER sort SET DEFAULT nextval('clients_sort_seq');

(or, we could do this when we create the table by just adding the
field then, which is much easier)::

  ...
    sort SERIAL NOT NULL
  ...

Then we'll make a simple change to our `clients_to_lines` function::

    /* get child records and concatenate into newline-sep text */

    CREATE OR REPLACE FUNCTION clients_to_lines (text) RETURNS text as '
       rv = plpy.execute( "SELECT client"
                        . " FROM Clients WHERE uid=''%s''"
			. " ORDER BY sort" % args[0])
       return "\\n".join([ ln["client"] for ln in rv ])
    '
      LANGUAGE plpython;

Now we're guaranteed to records back in the same order we inserted
them.


Creating a new storage class
============================

FIXME

Creating our subclasses type
----------------------------

FIXME

Improving fixed point type storage
----------------------------------

FIXME

Fixing image storage
--------------------

FIXME

Dynamically changing storage types
----------------------------------

FIXME, but for now::

  | You add "storage=PostgreSQLStorage()" on fields that you want
  | in the PostgreSQL database. This makes it easy to have some
  | fields stored in a PostgreSQL database and others in a Sybase
  | database. I realise this.
  |
  | Let's say that I store everything in PostgreSQL and then one day
  | I want to switch to Sybase. Then I'd have to change every
  | "storage=PostgreSQLStorage" to "storage=SybaseStorage".
  | What if the class had a 'storage' attribute that you could set
  | instead? Then you could only specify "storage=SQLStorage".
  |
  | I think most people only use one RDBMS? So then this would
  | be the simplest thing. And also if you want your new type public,
  | everyone won't probably use the same database. Then you'd
  | like to change a field in the ZMI to say that all relational database
  | fields should be stored with Sybase. Anyone agree?
  |
  | But I may be ranting about something that already exists?

  In fact there is an (undocumented) method to change storages. It is
  called (guess what?) setStorage, and it's a method of the Field
  class. So, if you have an existing object, and you want to migrate
  from one storage to another, you need to do something like this (in
  an External Method, of course):

  ----------------------------------------------------------------------
  from Products.Archetypes.Storage import SybaseStorage # Does not exist currently

  results = root.portal_catalog(dict(portal_type='MyObjectType'))
  for r in results:
     r.getObject().Schema()['fieldname'].setStorage(SybaseStorage())
  ---------------------------------------------------------------------

  Then you would shut down your zope instance and adjust the schema
  definitions accordingly. NOTE: After migrating your objects.

  You also need to make sure the column already exists in your
  databases.

from mail on the Archetypes-devel mailing ilst by Sidnei da Silva.


Integrating relational database schemas into Archetypes	
=======================================================

One interesting trick that could benefit us is using *schemas* with
Archetypes.

While many documents refer to a database schema as the definition of
its tables, views, etc., I'm referring here to the feature of
PostgreSQL that give a database multiple namespaces.

For example, in the database `mydb`, we could have only one table
called `ideas`. But if we create a new namespace (schema), we can put
this a new `ideas` table in the new namespace.

For example:

.. parsed-literal::

  database=# **CREATE TABLE Ideas ( idea text );**
  CREATE TABLE

  database=# **CREATE TABLE Ideas ( idea text );**
  ERROR:  Relation 'ideas' already exists

  database=# **CREATE SCHEMA More;**
  CREATE SCHEMA

  database=# **CREATE TABLE More.Ideas ( idea text );**
  CREATE TABLE

Now we have two independent tables called `ideas`, and can choose
which one to use by referring to it by namespace:

.. parsed-literal::

  database=# **INSERT INTO Ideas VALUES ( 'commute to work.' );**
  INSERT 116491 1

  database=# **INSERT INTO More.Ideas values ( 'go out with friends.' );**
  INSERT 116492 1

The tables are completely separate:

.. parsed-literal::

  database=# **SELECT \* FROM Ideas;**
	 idea
  ------------------
   commute to work.
  (1 row)

  database=# **SELECT \* FROM More.Ideas;**
	   idea
  ----------------------
   go out with friends.
  (1 row)

If you don't name a schema explicitly, PostgreSQL uses your *schema
path* to determine your schema. So, even before you knew you were
using schemas, you were! The default schema in most PostgreSQL setups
is the same name as the user, so I could see the "unnamed" ideas table
above as `joel.ideas`.

The interesting idea here is that we could have different database
adapters that have different connecting PostgreSQL users, each having
a different schema path. Then, depending on which database adapter I
used, I could see different results.

Or, even more interesting, we can ask PostgreSQL to change our schema
path for us by executing the SQL command `SET search_path=foo`, where
foo is our new, comma-separated search path. If we set our search
path differently, we could get different results. Useful ideas would
be to have the search path set differently based on who the logged in
user was, or what her or his roles were, etc.

Using this ideas we could implemented Archetypes-stored objects that
provided versioning or security capabilities that were dependant on
users or roles: the user `june` would see results from one table,
where `rebecca` would see results from another. All this would happen
transparently and quickly at the PostgreSQL level, without having to
put code for this in all your accessors in Archetypes.

Of course, we'd have to make sure inserts and deletes kept the tables
in sync, otherwise `june` would get an error trying to look at a ZODB
object for which there is no corresponding record in her schema's
table. But this syncronization would be fairly straightforward to
create using triggers on the tables.

There are no hooks currently in Archetypes SQLStorage to execute the
required `SET` command before the various SQL calls, but it would be
easy to implement this.

And, of course, this trick isn't specific to Archetypes--it's also
useful when working with relational databases in Zope the traditional
way with SQL Methods. It's particularly cool as an idea with APE--you
could make the ZODB reconfigure itself depending who the logged in
user is! [#]_

.. [#] In truth, though, I haven't tried this with APE, and I suspect
       you'd to test it thoroughly--there might be lots of nasty
       surprises if APE finds the ZODB changing underneath of it in
       unexpected ways. Or maybe not. Let me know if you try this out.


The status of SQLStorage
========================

SQLStorage is newer than Archetypes itself, and does not appear to be
as soundly developed and tested. In email to me, Alan Runyan said
that:

  NOTE: SQLStorage is incredibly inefficient.  It works quite well and
  we have done a project with it (that why it exists).  But really it
  should be rewritten if you are going to use it in a very large scale
  production environment.   I would consider the implementation
  'alpha' but stable. 
    
I have not had a chance to audit the code to see what the
inefficiencies are that he is referring to; however, as seen here,
there are several buglets that prevent SQLStorage from working
correctly (failing to catch deletion errors, failing to map lists
correctly, etc.)

By the time you read this, these errors may be corrected and
SQLStorage may be better-tested and more efficiently implemented. Stay
tuned!


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
