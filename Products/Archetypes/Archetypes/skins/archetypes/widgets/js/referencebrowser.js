// function to open the popup window
// pass various info to the popup
function referencebrowser_openBrowser(allowed_types, widget_id, multi, title, description)
{
    window.open('referencebrowser_popup?allowed_types=' + allowed_types + '&widget_id=' + widget_id +'&multi=' + multi + '&ref_title=' + title +  '&ref_description=' + description,'referencebrowser_popup','toolbar=no,location=no,status=no,menubar=no,scrollbars=yes,resizable=yes,width=400,height=500');                 
}

// function to return a reference from the popup window back into the widget
function referencebrowser_setReference(widget_id, uid, label, multi)
{
    // differentiate between the single and mulitselect widget
    // since the single widget has an extra label field.
    if (multi==0) {
        element=document.getElementById(widget_id)
        label_element=document.getElementById(widget_id + '_label')
        element.value=uid
        label_element.value=label
     }  else {
         list=document.getElementById(widget_id)
         // check if the item isn't already in the list
          for (var x=0; x < list.length; x++) {
            if (list[x].value == uid) {
              return false;
            }
          }         
          // now add the new item
          theLength=list.length;
          list[theLength] = new Option(label);
          list[theLength].selected='selected';
          list[theLength].value=uid
     }
}

// function to clear the reference field or remove items
// from the multivalued reference list.
function referencebrowser_removeReference(widget_id, multi)
{
    if (multi) {
        list=document.getElementById(widget_id)
        for (var x=list.length-1; x >= 0; x--) {
          if (list[x].selected) {
            list[x]=null;
          }
        }
        for (var x=0; x < list.length; x++) {
            list[x].selected='selected';
          }        
    } else {
        element=document.getElementById(widget_id);
        label_element=document.getElementById(widget_id + '_label');
        label_element.value = "";
        element.value="";
    }
}

