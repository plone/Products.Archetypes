This readme is temporary and documents the issues with the new ReferenceBrowserWidget:

08/26/04:

This widget works with reference fields similar to the original reference widget.
The widget inherits from ReferenceWidget so all it's properties can be used.
Right now, the addable feature doesn't work yet. Or maybe it does but I haven't tried
it yet. The widget's pt has a commented line that enables this. But I'm not sure if the addable
feature is interesting for this widget.

Example:

schema = BaseSchema +  Schema((
    ReferenceField('singleRef', 
                   multiValued=0,
                   allowed_types=(....),
                   relationship='...',
                   widget=ReferenceBrowserWidget(description='single ref')),
    ReferenceField('multiRef', 
                   multiValued=1,
                   allowed_types=...,
                   relationship='Rel2',
                   widget=ReferenceBrowserWidget(description='multi ref')) ,
    ReferenceField('singleRef2', 
                   multiValued=0,
                   relationship='..',
                   widget=ReferenceBrowserWidget(description='single ref2',)),    
                              ))

etc...

Both the templates are prototypes. There are still some inline styles, especially in the popup because
I didn't want to tweak with plone's css stuff and I didn't want to do hacking and tricking to incorporate
a stylesheet myself. So, that's still a point of interest.

Furthermore I made some design decisions. Right now, in the popup window, all objects are shown and
objects that may be referenced to are bold and the other objects are greyed out. I chose to show the
non-referenceable objects too because they may be an important part of the context that help
the user search for the desired objects to browse to.
Another thing that I chose for is that in case of a multi-value widget, the popup remains open so that you
can continue to add references without having to reopen the popup over and over again. Problem is that
you have to close the window yourself.

A thing that is more related to forms in general is that the items in the multiselect listbox need to be
selected before Save is clicked otherwise only the selected items are submitted. That kinda sucks
usability-wise because now the user basically has to make two selections: first by choosing the items in the
popup and secondly by selecting them again in the listbox. Right now I made it so that the items are selected
by default but if the user starts clicking in the list, then there might be an issue. Btw, the inandout widget
has the same problem.
Best would be to select all the items in a script just before the form is submitted so that the complete list
is submitted. But that requires changes in the base_edit form I think. But it's something to think about since
there are now already two widgets that needs to be prepared like this (inandout and this one, haven't looked
at picklist though, could have the same problem).

Anyway, have fun with it :-)

Danny Bloemendaal
danny.bloemendaal@companion.nl