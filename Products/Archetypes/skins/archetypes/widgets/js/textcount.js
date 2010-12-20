<!-- Original:  Ronnie T. Moore -->
<!-- Dynamic 'fix' by: Nannette Thacker -->
function textCounter(field, countfield, maxlimit) {
  var fieldval = jq(field).attr('value');
  if (fieldval.length > maxlimit) {
      // if too long...trim it!
      jq(field).attr('value',  fieldval.substring(0, maxlimit));
      alert( 'This field is limited to ' + maxlimit + ' characters in length.' );
  } 
  // update 'characters left' counter	
  jq('input[name="' + countfield + '"]').attr('value', Math.max(maxlimit - fieldval.length, 0));
}
