Known Issues
============

:Author: Sidnei da Silva
:Contact: sidnei@x3ng.com
:Date: $Date$
:Version: $Revision: 1.1 $
:Web site: http://sourceforge.net/projects/archetypes

Here you can find a list of known issues, contributed by users and
developers. We will try to keep this list always updated with the
current development and summarize the discussions on the `mailing
list`_.

.. _mailing list: http://sourceforge.net/mailarchive/forum.php?forum_id=32048

.. contents::


Large Files and FileField/TextField/ImageField
----------------------------------------------

In order to try to make Archetypes perform slightly better when
uploading/downloading large files, the FileField has been optimized to
store and return ``OFS.Image.File`` instances. This can be a problem
on the following case:

- You have a ``metadata`` entry on your catalog with a name that
   matches a field or a accessor on your archetype.
- Your have the said field using AttributeStorage
- You have your catalog on a mounted storage

The same can happen on ImageField and TextField, though YMMV. The
issue is that a Persistent object can end up in the ``ZCatalog``
metadata.

In this case, you may end up getting a 'Unable to store object from
foreign connection' (can't remember the exact spelling) error. To
solve this, you should probably do one of:

- Change your field to a ``StringField`` *or*
- Change your storage to ``MetadataStorage`` or some other storage
  that doesn't store into attributes with the name of the field.


ImageField generates "Decoder jpeg not available" error on OSX.
---------------------------------------------------------------

:Author: Gabriele Bozzi
:Contact: webmaster@fefsi.org

Problem
#######

You are under OSX and installed Plone binaries. You have been
fascinated by Archetypes and its easy way of managing document
types. Your custom Schema includes an ImageField occurence for your
next wonderful web project. But there is a problem: if you try to
create an instance of the newly defined Archetype OSX returns you with
the following annoyance::

  - Decoder jpeg not available -

Grrrrrr !!!! It took me all my Biblical  patience not to give up immediately (OSX is not what I would call the most plain Unix implementation.. But I love it !).

Explanation
###########

The current OSX Plone binary distribution (at writing time: 1.0.1) is
a complete standalone framework including Python 2.1.3 and its
libraries.  Even if the Python distribution is quite complete, it does
not seem neither to include the necessary Pyhton bindings for the PIL
(Python Imaging Library) nor the classic (read standard.) Zlib
extensions. The reason for this is maybe because OSX does not include
as standard the following libraries: `IJG Jpeg Library`_ and `zlib`_.

.. _IJG Jpeg Library: http://www.ijg.org
.. _zlib: http://www.gzip.org

The IJG Jpeg Lib is a general purpose library that provides C code to
read and write JPEG-compressed image while Zlib is the GNU zip
library.

Solution
########

Install from source Jpeg and Zlib libraries and recompile the PIL
against the Python that came in the binary OSX distribution.

I will report here just my experience on how I let things work hoping
that somebody having the same problems could find a solution.

Zlib
****

1. Download Zlib sources from http://www.gzip.org/zlib/zlib-1.1.4.tar.gz

2. On a temporary folder, for example::

    /Users/yourname/installers

3. Open a shell and put yourself in the folder mentioned above; perform
   the following commands (you can use sudo as listed or just log-in as
   superuser)::

    tar xfz zlib-1.1.4.tar.gz
    cd zlib-1.1.4
    ./configure
    make
    sudo make install

If everything went well you should exit with no error codes from the
compilation and install sequence.  Zlibs are installed in /usr/local/
and /usr/include.

Jpeg libraries
**************

1. Download jpeg sources from http://www.ijg.org/files/jpegsrc.v6b.tar.gz

2. On the same temporary folder as before and perform the following operations::

    tar xfz jpegsrc.v6b.tar.gz
    cd jpeg-6b
    ./configure
    make
    make test
    sudo make install
    sudo make install-lib

   This time the process is a bit longer but, again, you should not have
   any relevant error (if you have a stock-configured OSX) except the
   one mentioned later..  Check if the following files are present::

    /usr/local/lib/libjpeg.a.
    /usr/local/include/jpeglib.h

3. To avoid OSX to complain for having libraries not updated (if it did
   not already complain at the end of the install-lib step)::

    ranlib /usr/local/lib/libjpeg.a

PIL
***

This is the last step and, to a little extent, the one that needs just a few tweaks.

1. Download PIL sources from http://www.pythonware.com/downloads/Imaging-1.1.3.tar.gz [#]_

2. Again, perform from the temporary folder the following commands::

    tar xfz Imaging-1.1.3.tar.gz
    cd Imaging-1.1.3
    cd libImaging
    ./configure

3. After ./configure analyzed our OSX and generated the necessary rules
   for make to work we need to edit the resulting ImConfig.h file. I use
   vi for the "quick-and-dirties" but feel free to use whatever editor
   you like::

    vi ImConfig.h

   And change the following line::

    #undef HAVE_LIBJPEG

   in the following::

    #define HAVE_LIBJPEG 1

   Check also if the line::

    #define HAVE_LIBZ 1

   is present (it should). If not add it at the end of the file.

4. Save it and go on with the following shell commands::

    make

5. Make will complain with a warning::

    ranlib: file: libImaging.a(Dib.o) has no symbols

   Never mind and continue: it does not seem to be critical.

6. Now perform the following commands [#]_::

    cd ..
    PloneDirectory/ Python/bin/python setup.py build
    PloneDirectory /Python/bin/python setup.py install

7. You are done! To test the whole thing just perform this::

    cd ..
    PloneDirectory/ Python/bin/python ./Minitest/test.py

.. [#] As for the previous packages I am mentioning versions that are
   tested to work with Binaries 1.0.1 of the Plone distribution. Check
   which version you have in the future to avoid potential
   incompatibilities.

.. [#] PloneDirectory is the actual folder where your Plone has been
   installed.

For good measure I suggest to restart the machine (it's not
really needed but I still wonder how OSX does not get confused with
framework and classic libraries.. If you are not on a production
server (I guess you are not) you should have no problem doing this.

A lot of valuable resources and help can be found on the `python image
sig mailing list`_ where I found a message from calvin@xmission.com
that helped me much to verify my steps (initially I adopted another
approach but he gave me the "Satori" to rationalize the
installation). I would be delighted to credit him for this paper along
with me if I only knew the name of the guy (too lazy to contact him
!!?).

.. _python image sig mailing list: http://mail.python.org/pipermail/image-sig/

Happy Scheming with Archetypes (this product is just wonderful, I hope
it will be included in the next version of Plone).

