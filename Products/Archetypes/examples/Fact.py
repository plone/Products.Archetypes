from Products.Archetypes.atapi import *
from DateTime import DateTime
from Products.Archetypes.config import PKG_NAME

schema = BaseSchema.copy() + Schema((
    TextField('quote',
              searchable=1,
              required=1,
              ),

    LinesField('sources',
               widget=LinesWidget,
               ),

    TextField('footnote',
              required=1,
              widget=TextAreaWidget,
              ),

    DateTimeField('fact_date',
                  default_method=DateTime,
                  widget=CalendarWidget(label="Date"),
                  ),

    StringField('url',
                widget=StringWidget(description="A URL citing the fact",
                                  label="URL"),
                validators=('isURL',),
                ),
    ))

class Fact(BaseContent):
    """A quoteable fact or tidbit"""
    schema = schema


registerType(Fact, PKG_NAME)
