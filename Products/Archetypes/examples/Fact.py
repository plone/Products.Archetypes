from Products.Archetypes.public import *
from DateTime import DateTime

schema = BaseSchema + Schema((
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
                  default=DateTime(),
                  widget=CalendarWidget(label="Date"),
                  ),

    ObjectField('url',
                widget=StringWidget(description="A URL citing the fact",
                                  label="URL"),
                validators=('isURL',),
                ),
    ))

class Fact(BaseContent):
    """A quoteable fact or tidbit"""
    schema = schema


registerType(Fact)
