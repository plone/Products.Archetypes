====================================================
HOWTO: Using Archetypes SQLStorage and Advanced Tips
====================================================


Introduction
============

The SQLStorage storage for Archetypes_ allows you to transparently
store attributes of your objects in an SQL-backed database.

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

.. _PostgreSQL: www.postgresql.org

.. _Archetypes: www.sf.net/projects/archetypes

Archetypes Versus Other Relational Database Systems
---------------------------------------------------

The scope of what Archetypes accomplishes is similar to, yet very
different from, other systems of connecting Zope to relational
databases.

Archetypes stores the objects in the ZODB as an archetype object, having
traditional Plone/CMF/Zope methods such as Title(), absolute_url(), etc. However,
individual attributes (such as title, author, body, etc.) can be looked up in
and stored in the relational database. Since objects are real Zope objects,
they work naturally with acquisition, catalogs, and other Zope technologies.
Since you can choose which attributes to store in the relational database,
attributes that don't have a naturally tight fit with relational database
structures can be left in the ZODB, as can ones that might easily fit in a
relational database structure, but for which you have no external relational
database access requirements.

Versus ZSQL Methods
+++++++++++++++++++

A more traditional method of Zope/Relational Database connection has
been to store rows of information in a relational database, and create
ZSQL Methods to look up and display this information. With this
technique, you can associate a Python class with a relational database
row (this technique goes by the colorful name "pluggable brains"), but
the objects aren't real persistent Zope objects, and aren't found
during catalog calls. This strategy requires customized integration to
work with key Plone technologies such as acquisition, workflow,
portal_forms, etc.

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


Versus APE (formerly Adaptable Storage)
+++++++++++++++++++++++++++++++++++++++

Shane Hathaway's product APE_ (formerly called Adaptable Storage)
allows you to store your Zope objects in different formats (such as in
standard filesystem objects or on a relational database). In this
case, segments of the ZODB space are "mounted" from results in a
relational database. This means the entire object is on the ZODB--all
attributes, etc. Deleting an object from the relational database,
adding it, or modifying it effect the ZODB instantly since the this
part of the ZODB is just a mounted pointer the relational database.

While APE is a technological accomplishment, and very useful for some
projects, it doesn't fit perfectly into an existing natural database
role. All ZODB objects are stored in a few very APE-oriented tables,
rather than being stored in customizable,
traditional-relational-database tables.

In addition, APE works by location, rather than by type (as Archetypes
does).  That is, *everything* in the folder `/foo` is controlled
(mounted) by APE. If `/foo` contains all objects of a certain
portal_type (like Customers) you could treat these tables as the
"customer relational database", and work around the unusual
object-to-relational database table structure. However, if there are
different types stored in that directory, you end up with a mishmash
of different types of data stored in the same tables, and don't have
the straightforward setup of a "customer" table versus an "orders"
table, etc. [#]_ With Archetypes, each portal_type maps to an
individual table, regardless of where it is stored.

Lastly, APE does not have the integrated form
production/validation/editing systems that Archetypes does.

.. _APE: http://hathaway.freezope.org/Software/Ape

.. [#] It seems like APE supports custom object marshallers and unmarshallers
   to create different table types for different object types; however,
   at this point, I haven't been able to find working examples of this
   that I could understand and apply.


Created a Database-Stored Object
================================

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
the traditional metadata attributes that are brought in by the
BaseSchema). This object would be stored entirely in the ZODB by
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

Now, we before we can begin using this object, we must do two things:

- Add a database connector (in our case, PostgreSQL) to our site. We
  can use any PostgreSQL adapter; however, I've used ZPyscopgDA_ for
  testing this, as this appears to be the best maintained of the
  noncommercial adapters.

.. _ZPyscopgDA: http://initd.org/software/psycopg

- In the `archetype_tool`, under the `Connections` tab, we need to set our
  database connector for this type of object to our new database connector.
  Note that in this tab, we have a `default` connection, and we can override
  this for an portal_type that uses SQLStorage. In our case, you can either
  set the default to the new connection, or the specific connection for our
  ExampleObject.

Before you go any further, make sure that the user you defined in your
database connection has the ability to create tables, and insert,
update, and delete from tables in your database. [#]_

.. [#] In real life, it isn't neccessary that the user have to have
   `CREATE TABLE` privileges, as you can create the table yourself before
   Archetypes tries to. However, it's easiest to let Archetypes create
   the table for you. In which case a good strategy is to grant
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
examine the database::

  database=# \d
                    List of relations
   Schema |           Name           |   Type   | Owner
  --------+--------------------------+----------+-------
   public | customersql              | table    | joel

Archetypes has created our table for us. Examine the table::

  database=# \d customersql
    Table "public.customersql"
    Column   | Type | Modifiers
  -----------+------+-----------
   uid       | text | not null
   parentuid | text |
   body      | text |
   phone     | text |
  Indexes: customersql_pkey primary key btree (uid)

Notice that Archetypes has created our `body` field as text field and
the `phone` field as a text field. These transformations are part of
the PostgreSQLStorage method, and can be easily changed in the source,
should your needs require different mappings. [#]_

Also, notice that there are two new fields created:

- **UID** `(uid)`: this is a unique identifier for your object

- **Parent UID** `(parentuid)`: this is the unique identifier (if any)
  for the parent (enclosing) container for your object.

.. [#] Or you can create the table in advanced of Archetypes, and
   choose whatever field types you want, as long as your database can
   cast Archetypes values into your field types. For instance, in our
   example, though `text` is an acceptable choice for phone numbers,
   we might prefer to have this stored as a `varchar(20)`. We could
   have created the table ourselves and made this choice; when
   Archetypes goes to insert a `text`-type value into phone,
   PostgreSQL can cast this to `varchar(9)`


About UIDs
==========

One of the smartest things about Archetypes is that it introduces the
ideas of unique identifiers into CMF sites. Zope IDs must be unique
within a folder, but need not be unique across a site. Therefore,
keeping track of the fact that you have an object called `Eliot` isn't
useful, since you may have several objects called that in different
folders.

A common workaround has been to refer to objects by their path (eg,
`/animals/cats/Eliot`), but this is fragile, since any change to the
object ID, or the IDs of any of the parent objects will change the
path and break these references.

Archetypes assigns each object a unique ID at creation [#]_, and then
maintains a mapping of that unique ID to the current location of the
object in the ZODB.  If the object is deleted, Archetypes will remove
it from its UID mapping.

.. [#] The IDs that are created are in the Plone default style, eg
   PortalType.2003-07-23.4911

Therefore, when our object was created, it will get a UID like
`Customer.2003-07-23.4911`. Even though we may change the object ID to
`new_example`, it will keep it's UID for the lifetime of the object.

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
                    if IReferenceable.isImplementedBy(o):
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
relationship in Plone.


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

  CREATE TABLE Order
    ( orderid SERIAL NOT NULL PRIMARY KEY
    , custid INT REFERENCES Customer
    ... other order fields ...
    );

The `order` table `custid` is the reference (called a `foreign key`)
to the `customer` table `custid`.

In Archetypes, we can just create two types: `CustomerFolder` and
`Order`.  Both of these will get UIDs from Archetypes. But if we
change our `Customer` type to become folderish (ie derived from
Archetypes's `BaseFolder` rather than `BaseContent`), it can contain
objects, and we can add `Order` objects inside of it. These `Order`
objects will have their Parent UID field set to the `CustomerFolder`
UID, giving us an easy way to write ZCatalog queries for all orders
with a certain customer UID, or SQL queries asking the same thing.

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

Our Order type is straightforward. It will include the cost of an order, and
shipping details::


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

As of the writing of this HOWTO, Archetypes does not show a "folder
contents" tab for folderish objects like our
`CustomerFolder`. However, you can go to this view manually by
visiting the new customer folder object, and changing the end of the
URL to point to `folder_contents`. [#]_

.. [#] And you can add this to the type so that it naturally shows up by
   adding it to `portal_type`'s actions for this type.

Inside of the new customer folder, add an `Orders` object and enter
details.  Then, examine the `orders` table in the database::

  database=# SELECT * FROM Orders;
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
traditional primary key/foreign key setup than the Archetypes
UID. Many databases use a serial column [#]_ (integers that increase
for each new record) as a primary key.

.. [#] MySQL calls these integer columns with autoincrement feature.

To this with Archetypes, you can simply either:

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


If You Need A Very Different Table Structure
--------------------------------------------

Instead of having Archetypes write to the real table, we can have
Archetypes insert to a `view` of the table. Such a view can have
fields that looks like Archetypes expects, but actually insert the
information in different places and different ways.

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


Using Traditional Referential Integrity For the Child Table
-----------------------------------------------------------

For our `orders` table, we can do the same thing to give it a more
relational database natural serial primary key. However, it's likely
that we want to child orders table to relate to the parent
`customerfolder` table by the new `customerid` rather than the
Archetypes-oriented Parent UID.

To do this, let's create a `customerid` field to the `order` table::

  abort; commit;

  ALTER TABLE Orders ADD customerid INT;

  UPDATE orders
    SET customerid = Customerfolder.customerid
    FROM Customerfolder
    WHERE Orders.parentuid = Customerfolder.uid;

  ALTER TABLE Orders ALTER customerid SET NOT NULL;

  ALTER TABLE Orders ADD FOREIGN KEY (customerid) REFERENCES Customerfolder;

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
called NEW which reflects the new record being inserted (or for an
update, the new record to be written). Functions in PostgreSQL can be
written in different languages, including Python; for our example,
however, we'll use PostgreSQL's built-in PL/PgSQL language, a
PL/SQL-like language that is simple to write and understand.

Before you can write PL/PgSQL functions, you must enable this by
adding this language to your database. From the shell::

  $ createlang plpgsql your_db_name

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
tests, use the real UID of one of your `CustomerFolder` objects)::

  database=# insert into orders (uid,parentuid) values ('test', 'CustomerFolder.2003-07-23.4609');
  INSERT 35162 1
  database=# select uid, parentuid, customerid from orders;
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
delete a customer that has related orders, we'll get an error::

  database=# DELETE FROM Customerfolder;
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

This is because Archetypes 1.0beta doesn't deal properly with deletion
exceptions. Archetypes issues an SQL delete on the staff record, but
since there are related children, it will fail. This raises an
exception, but Zope only stops a deletion on a particular
exception--others just get logged and ignored. Therefore, the database
record can't be deleted (your database will refuse to do this,
regardless of how Zope asks), but the pointer to it in the ZODB will
be deleted. So the staff member won't be visible on the site, but the
data will stay in the relational database.

To fix this, apply the patch included with this howto. This raises the
proper exception (`BeforeDeleteException`) if the SQL deletion call
fails, which causes the Plone object deletion to fail. Unfortunately,
you'll get an standard error message, rather than a polite
explanation, but this is better than silently ignorining the database
failure and moving on. [#]_

This patch was developed for the beta version of Archetypes. This fix
may be included by the time you read this HOWTO. If so, please let me
know, and I'll update this section.

.. [#] If you want to make a nicer deletion error message, you could
   modify the standard_error_message method.


Cascading
+++++++++

PostgreSQL and most other databases that support referential integrity
can handle deletion of parent records in other ways. The default is to
block the deletion of parent with related children, but you can also
opt to automatically delete the children when a related parent is
deleted.

This option is called "cascading" a deletion. To set this up, we'd
create our child table differently::

  CREATE TABLE Child (
    childid SERIAL NOT NULL PRIMARY KEY,
    parentid INT NOT NULL REFERENCES Parent ON DELETE CASCADE
                                            ^^^^^^^^^^^^^^^^^
    ...
  );

Now, when the parent is deleted in the database, it will delete the
related child records rather than raising an exception.

Of course, this won't automatically delete the Zope ZODB objects for
the children, but the next section of this tutorial deals with the
question of how to have operations in the database "notify" Zope of
changes to make in the ZODB.


Missing Capabilities
====================

Sometimes in Zope projects, the changes all come from the Zope
interface, and the relational DB storage is just to soothe
ZODB-nervous customers, or to allow reporting from standard SQL
tools. In this case, the setup we have would be acceptable.

In cases where changes must propagate to Zope, here are some problems
we need to solve:

- Records that are inserted directly into the database are never
  visible to Zope, as ZODB objects aren't instantiated for these records.

- Records that are deleted directly in the database are never deleted
  from Zope. Therefore, ZODB objects will remain in the database that
  point to non-existant data that should be in the relational
  database. At this time, Archetypes raises an error if you try to
  view these objects.


- Records that are changed in the database **are** visible immediately
  to Zope, but any Catalog entries won't be updated, making Catalog
  calls incorrect.


Forcing Catalog Reindexes on Update
-----------------------------------

There's no way for our database to directly affect Zope. Instead, we'd
have to either make a request that the ZServer hears and passes on to
our application, or we'd have to write a standalone Python program
that connects to the ZODB to make these requests.

The latter can be very slow (connecting to the ZODB can take a while),
and would only work on the machine that the ZODB is hosted on, where
the first choice is ZEO-friendly, remote database machine friendly,
and generally easier and faster.

By creating a custom function in PostgreSQL, we can execute a Web or
XMLRPC request to reindex the catalog.

We'll need a bit of Zope support: Zope will be given the UID for the
record that has changed, and needs to find the real Zope object, and
call reindexObject() on it.

We could do this by adding a method to ArchetypesTool.py (which is not
a bad idea!), but, for simplicity's sake, we'll implement as a
PythonScript::

  # "reindex_by_uid"

  ## Parameters: uid

  o = context.archetype_tool.lookupObject(uid)
  o.reindexObject()
  return "ok"

You can test calling this by giving it a UID.

Functions can be written in several languages in PostgreSQL, including
Python.  However, making a web request is an "unsafe" act in
PostgreSQL, so we need to use an untrusted language, rather than a
trusted language. At this time, the Python language is implemented as
a trusted language (though this is changing in PostgreSQL 7.4 and is
already checked into CVS), and the easy-to-use PL/PgSQL that we used
earlier doesn't have commands to make web requests.

Therefore, we'll use Perl's untrusted language, plperlu. [#]_

.. [#] In PostgreSQL 7.4, all of the examples provided could be done
   in PL/Python, which is untrusted (allowing imports of any module)
   and can be a trigger function language. In earlier versions of
   PostgreSQL, you could do this by recompiling PL/Python after adding
   the required-for-import modules to the list of acceptable
   modules. Since this might be tricky for non-PostgreSQL-gurus, the
   examples in this HOWTO are written using PL/Perl and SQL.

Make sure that Perl untrusted functions are enabled for your database::

  $ createlang plperlu your_db_name

Then, in psql, we'll create a function that uses `wget`, a common,
simple command line http request tool::

  CREATE OR REPLACE FUNCTION reindex_by_uid (text) RETURNS text as '
    $_ = shift;
    $sec = "--http-user=joel --http-passwd=foo";
    $portal = "/arch";
    $server = "localhost:8080";
    $rc = `/usr/bin/wget $sec -q -O - http://$server/$portal/reindex_by_uid?uid=$_`;
    return $rc;
  ' LANGUAGE plperlu;

The `-q` option to wget tells it to be quiet, ie, not to output
progress reports, etc. The `-O -` options tells it to write the result
page to standard output.

Of course, you'll want to replace the `localhost:8080` with your
server name and, if needed, port number, and replace the portal
variable with the path to your portal object. In addition, you'll
probably need to either make sure the Zope script is accessible to
anonymous users and and proxied to Manager (so it can reindex any
content), or pass a Manager-level username and password to Zope by
putting the username and password in as shown above.

Now, in PostgreSQL, if we update a record, we can force a reindex by
calling this, as in::

  database =# SELECT reindex_by_uid('...');


Using Triggers to Automate This
+++++++++++++++++++++++++++++++

Of course, we'll want to have this happen automatically when we update
a record. To do this, we'll write a trigger in PostgreSQL that
triggers whenever an update is made to our customer table.

To do this, we need a trigger function that is called when our table
is changed. In a perfect world, we could use our Perl function,
above. However, at this time, Perl functions can't be used as trigger
functions (though Python and other language functions can). Since we
use PL/PgSQL functions earlier, we'll use another here::

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
and calls the reindexing. It seems like a lot of redirection, but
works fine. Go test it out. Make a change to your object's body field
directly via PostgreSQL, then check the catalog results and see that
the appropriate field (in this case, SearchableText) has been updated.


Forcing Deletes and Inserts
---------------------------

*(For advanced readers, since some of the detail is left to you to
fill in).*

Inserts
+++++++

Inserts would be handled the same way: write a Zope PythonScript that
creates the object, it being passed the different fields
required. Then write a plperlu function that crafts a wget statement
that calls our Zope PythonScript, then a trigger to actually call this
upon inserts.

First, we'll want to create a PythonScript that will create our
content for us. The trickiest part is coming up with a good, unique
UID. If we knew that something in our table that was being inserted
was unique, we could use that (prepended by the type name); however,
to look and feel consistent with UIDs created through the web, we'll
copy in the same UID-generating code that Plone itself uses.

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

The difference is that we don't really want to do an insert in the
database, though--when Zope does it's object creation, it will create
the database record itself in Archetypes. So we want our DB insert not
to happen.

We could do this with a trigger, and have the trigger raise a failure
so the insert didn't happen. This, though, would be confusing for the
user, who would see an error message, and, if we were in the middle of
transaction, would spoil that transaction, aborting it and preventing
other actions from happening in the relational database. A better
solution, then, would be to use a feature of PostgreSQL called
`rules`, which we saw briefly earlier `If You Need A Very Different
Table Structure`_.

Rules are rewritings of a query to do anything instead of the
called-for-query. We'll "rewrite" our INSERT query to a SELECT query,
which in this case will SELECT the plperlu function that wget's the
Zope function to create object.

Rule creation is covered in the PostgreSQL documentation. Our rule
will be::

  CREATE RULE customer_ins AS
    ON INSERT TO Customerfolder
    WHERE NEW.uid = 'direct'
    DO INSTEAD (
      SELECT customerfolder_add ( NEW.body, NEW.phone );
    );

Now, when you want to insert a record directly, you can do so like::

  INSERT INTO customer_ins ( uid, body, phone )
    VALUES ( 'direct', 'body goes here', '555 1212' );

The `WHERE NEW.uid = 'direct'` clause is required to prevent Zope's
insertion from trigger our rule which would trigger Zope's insertion
... and so on into permanent recursion. Any attempt to insert a record
with a `UID` not equal to "direct" will go directly into the database
without triggering any action from Zope.


Deletes
+++++++

Deletes would be handled like inserts, but our PythonScript would
obviously do the deleting for us instead.

Details here can be figured out the reader, but you'll need a
PythonScript to handle the deletion, a plperlu function to craft the
proper `wget` command, and a trigger that handles `ON DELETE`.

Since we can't stop recursion from happening with a DELETE the way we
can with an INSERT, we should have our trigger call Zope not just as
`DO INSTEAD` but `DO`, so the Zope deletion happens and the normal
PostgreSQL deletion happens.  When the Zope deletion tries ...

XXX FIXME XXX


Inserting a Child Record
++++++++++++++++++++++++

If we want to allow direct database insertion of the child `Orders`
objects, we have to add one additional wrinkle: the `Orders` objects
are meant to be physically contained in their related parent
`Customer` object. Therefore, our PythonScript that would add their
child `Orders` record must make the context for the `invokeFactory`
call be the enclosing `Customer` context.

We could accomplish this easily by passing the child `Orders`
PythonScript add helper the `UID` of the `Customer`, and it could
lookup the `Customer` object (using the API demonstrated earlier for
looking up an object given its UID). Then we could use that context
for our `invokeFactory` call.



Changing SQLStorage's Storage Methods: An Example With Lists
============================================================

Creating the Types and Fixing the Mapping
-----------------------------------------

If we add a list type to our customer object, we run into a snag with
marshalling and unmarshalling.

Let's add the object type::

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

Put this in the schema, and restart Archetypes.

As we're storing this in the ZODB (not in the relational database),
everything works fine. The form widget is a textarea than is given
newline-separated entries, which are converted by Zope to a list and
stored as an attribute of the object.

If we create a new archetype type that contains this list ("lines")
field and tries to store in the relational database, we have problems.

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

We can fix this problem by patching `SQLStorage.py` to do the right thing and
create a `text` field, or we can simply create the table in advance before
Archetypes tries to do so.

Creating the table in advance is easily done::

  CREATE TABLE Customerlistsql (
      uid text NOT NULL PRIMARY KEY,
      parentuid text,
      body text,
      phone text,
      clients text
  );

Or we can change the type mapping that Archetypes does. You can do
this either by editing `SQLStorage.py` and making changes for your
database type, or, if you'd rather not modify the Archetypes source
code, you can subclass your storage type, make the changes there, and
use this new subclassed storage type.


The change we want is in the dictionary `db_type_map`, which translates an
Archetypes field type into the relational database field type. As of this
writing, there is no translation for `lines`, so Archetypes uses `lines` as
the relational database field type. We'll add a translation for `lines` to
become `text`::

    db_type_map = {
        'object': 'bytea',
        'file': 'bytea',
        'fixedpoint': 'integer',
        'reference': 'text',
        'datetime': 'timestamp',
        'string': 'text',
        'metadata': 'text', # eew
        'lines':'text', # still requires some help, though!
        }

If you restart Archetypes and try to add your object now, it will
create the table and let you create objects.

Fixing the Translations
-----------------------

A serious problem still persists, though.

The newline-separated entries (the "lines") are turned into a list by
Archetypes, such as::

  [ 'Cat', 'Dog', 'Bird' ]

but SQLStorage attempts to store this list directly in the
database. This ends up a string containing the literal value
"['Cat,'Dog','Bird']" which is stored in the database::

  database=# SELECT uid, clients FROM Customerlistsql ;
                 uid               |        clients
  ---------------------------------+------------------------
   CustomerListSQL.2003-07-23.1619 | ['cat', 'dog', 'bird']
  (1 row)


Unfortunately, this is a difficult format to work with in the
database, and not handled correctly coming out by Archetypes. When you
view the attribute through Zope, it sees it as a single string, rather
than a list, and shows it as::

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

There are hooks in Archetypes for this: any function called map_*XXX*
is called when storing field type *XXX* and a method called
unmap_*XXX* is called when retrieving field type *XXX*.

Our mapping will convert this list back to a newline-separated string,
and pass this to the database::

    def map_lines(self, field, value):
        return '\n'.join(value)

Our unmapping method will convert the newline-separated string back to
a Python list:

    def unmap_lines(self, field, value):
        return value.split('\n')

Both of these should go into SQLStorage class as methods of SQLStorage
class or of your particular relational database's storage class. If
don't want to (or can't) modify the source to Archetypes, you could
subclass your storage class, add the methods to the subclass, and have
your object schema fields use your new, subclass storage type.

Now, we can transparently work with our lists: they appear on the form
as a newline-separated string (so we can easily edit them in a
textarea), they're handled in Zope as a Python list object (so we can
work naturally with them and don't have to be concerned with how
they're stored), and they're stored in the database as a simple
newline separated list so we can access them simply in the database.

Even Better: Turning Into Arrays
--------------------------------

While our solution above lets Archetypes store the data and get it
back in one piece, it isn't great in the relational database: most
relational database querying programs and reporting programs are
ill-equipped to deal with searching for values that are stuffed into
text fields.

To find all customers that have two values, "fish" and "cat", in clients, you could write
queries like::

  SELECT * FROM Customerlistsql
    WHERE clients LIKE '%cat%fish'
      OR clients LIKE 'fish%cat'

but this is ugly, slow, unindexable [#]_, and becomes unmanagable as
you add more predicates to the logic.

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

First, let's change our table structure to use arrays::

  database=# ALTER TABLE Customerlistsql DROP CLIENTS;
  ALTER TABLE

  database=# ALTER TABLE Customerlistsql ADD CLIENTS text[];
  ALTER TABLE

We can test out the array storage works directly in PostgreSQL by
updating an existing record and examining it::

  database=# UPDATE Customerlistsql SET clients='{cat,dog,bird}';
  UPDATE 1

  database=# SELECT uid, clients FROM Customerlistsql ;
                 uid               |    clients
  ---------------------------------+----------------
   CustomerListSQL.2003-07-23.1619 | {cat,dog,bird}
  (1 row)

  database=# SELECT uid, clients[1] FROM customerlistsql ;
                 uid               | clients
  ---------------------------------+---------
   CustomerListSQL.2003-07-23.1619 | cat

Now we can change our `map_lines` and `unmap_lines` methods, above, to
write out and retrieve values written in this format::

    def map_lines(self, field, value):
        return "{%s}" % ','.join(value)

    def unmap_lines(self, field, value):
        return value.strip("{}").split(',')

**Please note** that these are very naive implementations, as they do
not deal with the possibility that a list item might have a comma in
it. It would be quite easy, though, the write versions that quoted the
comma and unquoted it for unmapping.

Restart Archetypes to pick up the changes to the storage type, then
edit an existing or add a new object. Notice how the values you put
into the `clients` field end up as array in PostgreSQL, and are read
correctly.


Turning lists into related child records
----------------------------------------

While the last section works wonderfully, not everyone is lucky enough
to work with PostgreSQL, the "World's Most Advanced Open Source
Database". Many databases don't support a notion of arrays.

In this case, or even when using PostgreSQL, you can store the
individual client items as child records. We could, of course, do this
in Archetypes: have the customer be folderish, and add independent
client objects, as we did earlier for `Orders`. In some cases, as with
`Orders`, this makes sense: the child record has more than one piece
of information to it, you want to have a customizable way for
Archetypes to let users edit this information, etc.

In many cases, though, this would be overkill and annoying for the
user. For keeping track of a simple list of names or such (as our
examples for the clients field have been), having to add separate
objects is burdensome from a UI perspective, and creates additional
Zope objects that aren't really needed.

Rather, we'll keep our simple, clean `lines` interface, but
dynamically create and delete child records in a related table as
needed.

We'll store these list items in a related table, called clients::

  CREATE TABLE clients ( uid TEXT NOT NULL
                       , client TEXT NOT NULL
                       , PRIMARY KEY ( uid, client ) );

(the last line in this statement makes the primary key a *compound
primary key* composed of both the `uid` and `client` fields. We can
have multiple children for each parent UID, and different parents can
have the same client value, but each child can have the same client
only once. If it makes sense in your application that the same item
could appear in the list more than once, remove this restriction.)

What we want is a incoming function that will take the
newline-separated string and create child records for each line, and
an outgoing function that will turn child records back into a
newline-separated string.

So far, we've done coding in PostgreSQL in PL/PgSQL and plperlu. We
could do this in either of those languages. PL/PgSQL has very poor
string handling, though, so we'll rule that out. Instead of coding
more Perl, let's take a chance to try out Python coding in PostgreSQL.

First, make sure that plpython is enabled for your database::

  $ createdb plpython your_db_name

Then, let's add a Python function that, given the `uid` and
newline-separated lines field, adds the child records::

  /* split newline-sep text and insert into child table */

  CREATE OR REPLACE FUNCTION lines_to_clients (text, text) RETURNS integer as '
     plan = plpy.prepare( "INSERT INTO Clients VALUES ( $1, $2 )",
       [ "text", "text" ] )
     plpy.execute("DELETE FROM Clients WHERE uid=''%s''" % args[0])
     for ln in args[1].split("\\n"):
           plpy.execute(plan, [ args[0], ln ])
     return 1'
        LANGUAGE plpython;

First, we delete any existing clients associated with this
`uid`. Then, we iterate over the list, and inserts a client for each
entry. You can find out full information about using plpython with
PostgreSQL at plpython_.

.. _plpython: http://www.postgresql.org/docs/7.3/interactive/plpython.html

We can try out our function to make sure it works::

  database=# SELECT lines_to_clients('a','one\ntwo\nthree');
   lines_to_clients
  ------------------
                  1
  (1 row)

  database=# SELECT * FROM Clients;
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

And we can test that::

  database=# select clients_to_lines('a');
   clients_to_lines
  ------------------
   one
  three
  two
  (1 row)

We can see that our individual records are returned as one row of
newline-separated text.

To use this, though, we'll need for PostgreSQL to return the result of
`clients_to_lines` when Archetypes selects from the table so we'll
need to use a view instead of our table. Views are discussed earlier
in this document, in `If You Need A Very Different Table Structure`_.

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
database wouldn't know what to call this field, and Archetypes
couldn't find it.

Next, we'll create the update rule. This is called when you try to
update the view. It performs a normal update, then does calls our
inserting function::

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

We can test this out::

  database=# UPDATE customerlistsql SET clients='dog\ncat';
   lines_to_clients
  ------------------
                  1
  (1 row)

  joel=# SELECT uid, clients FROM customerlistsql;
                 uid               | clients
  ---------------------------------+---------
   CustomerListSQL.2003-07-23.1619 | cat
  dog
  (1 row)

Again, we can ignore the `SELECT` results we get from our
`UPDATE`. This is because our function is returning some information,
even though it's not useful to us.

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

We can test this in PostgreSQL to see that it works::

  database=# INSERT INTO customerlistsql ( uid
                                         , parentuid
                                         , phone
                                         , body
                                         , clients )
                                  values ( 'b'
                                         , 'c'
                                         , '555-1212'
                                         , 'body'
                                         , 'one\ntwo\npickle\nshoe' );
   lines_to_clients
  ------------------
                  1
  (1 row)

  joel=# SELECT * FROM customerlistsql WHERE uid='b';
   uid | parentuid | body |  phone   |       clients
  -----+-----------+------+----------+---------------------
   b   | c         | body | 555-1212 | one
  pickle
  shoe
  two
  (1 row)

  joel=# SELECT * FROM clients WHERE uid='b';
   uid | client
  -----+--------
   b   | one
   b   | pickle
   b   | shoe
   b   | two
  (4 rows)

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

And we can test this last piece in PostgreSQL::

  database=# DELETE FROM customerlistsql WHERE uid='b';
  DELETE 1

  database=# SELECT * FROM customerlistsql WHERE uid='b';
   uid | parentuid | body | phone | clients
  -----+-----------+------+-------+---------
  (0 rows)

  database=# SELECT * FROM clients WHERE uid='b';
   uid | client
  -----+--------
  (0 rows)

As mentioned in the comments, the delete rule would not be neccessary
if you have referential integrity on the `customerlistsql` and
`clients` tables; then you could either block deleting a
`CustomerListSQL` object if it had any related clients, or you could
cascade the deletion. Since this is a small, related table that is
meant to change everytime someone edits the `CustomerListSQL` object,
cascading seems more likely.

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


The Status of SQLStorage
========================

SQLStorage is newer than Archetypes itself, and does not appear to be
as soundly developed and tested. In email to me, Alan Runyan said
that:

  NOTE: SQLStorage is incredibly inefficient.  It works quite well
  and we have done a project with it (that's why it exists).  But really
  it should be rewritten if you are going to use it in a very large
  scale production environment.   I would consider the implementation
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
Free Documentation License, and the only invariant section is this
one, `About this Document`_. As such, you can distribute it, make
changes to it, etc.

.. _`Joel Burton`: mailto:joel@joelburton.com

If you have any comments, corrections, or changes, please let me know.
Thanks!

# vim:tw=78
