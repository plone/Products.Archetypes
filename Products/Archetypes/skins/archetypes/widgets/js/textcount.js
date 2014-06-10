<!-- Original:  Ronnie T. Moore -->
<!-- Dynamic 'fix' by: Nannette Thacker -->
function textCounter(field, countfield, maxlimit) {
  var fieldval = jQuery(field).attr('value');
  if (fieldval.length > maxlimit) {
      // if too long...trim it!
      jQuery(field).attr('value',  fieldval.substring(0, maxlimit));
      alert( 'This field is limited to ' + maxlimit + ' characters in length.' );
  } 
  // update 'characters left' counter	
  jQuery('input[name="' + countfield + '"]').attr('value', Math.max(maxlimit - fieldval.length, 0));
}
