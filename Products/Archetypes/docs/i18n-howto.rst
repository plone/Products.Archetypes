=====================================================
How to develop multi-language systems with Archetypes
=====================================================

:Author: Sidnei da Silva
:Contact: sidnei@x3ng.com
:Author: Sylvain Thenault
:Contact: syt@logilab.fr
:Date: $Date: 2003/07/03 09:31:50 $
:Version: $Revision: 1.3 $
:Web site: http://sourceforge.net/projects/archetypes

This document describes how to build objects that support multiple languages,
both for the management interface and for storing i18n-ized content.



i18n-ized interface
-------------------

Having i18n-ized interface means that templates which display your
content will be internationalized. But the dynamic data displayed by
the templates isn't necessarily internationalized (this is `i18n-ized content`_) 
Multiple languages in the interface is handled by the translation
service.

FIXME : to finish



i18n-ized content
-----------------

Having i18n-ized content means that your objects may have some
multilinguage data. It's a field based translation system, so you can
have field which can not be translated and fields which can.
You can get an example of an i18n aware content type in the examples
directory of the Archetypes distribution (I18NDDocument).


Defining your schema
````````````````````

To have a class which support I18N content, you should :

  1. make your object derives for from I18NBaseContent or
     I18NBaseFolder instead of BaseContent or BaseFolder. That'll add
     two actions to your content type : translate and
     translations. The one is a form to add / update translations of
     your contents. The second is to manage existing translations.

  2. using I18NBaseSchema instead of the standard BaseSchema if you
     want internationalized title and description (that's usually the
     case...). Note that I18NBaseSchema == I18NBaseContent.schema ==
     I18NBaseFolder.schema.

  3. use the "I18N" prefixed version of field classes for the
     internationalizable fields in your schema. Available i18n fields
     are : I18NStringField, I18NMetadataField, I18NFileField,
     I18NTextField, I18NLinesField and I18NImageField.

  4. everything else should works like for standard content :)


Make the catalog working with the multilingual content
``````````````````````````````````````````````````````

If you want to have a correct catalog support for your
internationalizable fields, you have to use the I18NTextIndexNG index
for those fields. To do so, go to your portal_catalog on the "indexes"
tab and replace existent indexes with a I18NTextIndexNG index (you
should reindex those fields if you previously had some content
indexed). Now your i18n content will be correctly indexed. Search on
i18n fields should only return objects whitch match the query and have
a translation for the current language used.


Add the i18n language selector box
``````````````````````````````````

You can simply do that by adding the following macro to your left or
right slot property : "here/i18n_slot/macros/i18nContentBox".
