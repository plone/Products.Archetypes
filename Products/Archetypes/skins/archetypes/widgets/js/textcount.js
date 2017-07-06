// Original:  Ronnie T. Moore
// Dynamic 'fix' by: Nannette Thacker
function textCounter(field, countfield, maxlimit) {
  var fieldval = jQuery(field).val();
  var counterElem = jQuery('input[name="' + countfield + '"]');
  if (fieldval.length > maxlimit) {
    // if too long...trim it!
    jQuery(field).val(fieldval.substring(0, maxlimit));
    counterElem.css('border-color', 'red');
  } else {
    counterElem.css('border-color', '#ccc');
  }
  // update 'characters left' counter
  counterElem.val(Math.max(maxlimit - fieldval.length, 0));
}
