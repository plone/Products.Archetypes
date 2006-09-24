==============================
Archetypes Documentation Guide
==============================

:Author: Sidnei da Silva
:Contact: sidnei@x3ng.com
:Date: $Date$
:Version: $Revision: 1.2 $
:Web site: http://sourceforge.net/projects/archetypes

This guide's purpose is to help developers to mantain some level of
organization on how to write docstrings and how to keep documentation
updated all the time.

Main documentation
==================

The entry point for documentation in archetypes is the `Archetypes
Quick Reference Guide`_. It is mantained as a reStructuredText
document inside the ``docs`` directory of the Archetypes module in
CVS. Its purpose is to serve as a guide for newbies that want to learn
how to use Archetypes to build their custom objects and as a reference
of the features available.

.. _Archetypes Quick Reference Guide: http://plone.sourceforge.net/archetypes/quickref.html

Docstrings
==========

Starting from the 1.0 release, we are requiring all docstrings to be
written using reStructuredText, so they can be extracted using the
`Docutils`_ package. That will generate a API guide to be used in
conjunction with the `Archetypes Quick Reference Guide`_.

`PEP 257`_ and `PEP 258`_, specially the section about the `Python
Source Reader`_, are a **MUST READ** for all developers and
contributors.

.. _Docutils: http://docutils.sf.net
.. _PEP 257: http://www.python.org/peps/pep-0257.html
.. _PEP 258: http://www.python.org/peps/pep-0258.html
.. _Python Source Reader: http://www.python.org/peps/pep-0258.html#python-source-reader


Additional Documentation
========================

Additional documentation must be provided in the case where a feature
or functionality is important enough and big enough not to fit in the
Quick Reference. An example of this is the `Archetypes i18n How-to`_,
which describes how to build objects that support multiple languages
both for the management interface and for storing i18n-ized content.

.. _Archetypes i18n How-to: http://plone.sf.net/archetypes/i18n-howto.html

