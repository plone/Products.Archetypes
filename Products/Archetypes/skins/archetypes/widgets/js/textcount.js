<!-- Original:  Ronnie T. Moore -->
<!-- Dynamic 'fix' by: Nannette Thacker -->
function textCounter(field, countfield, maxlimit) {
  var fieldval = jQuery(field).val();
  var countfield = jQuery('input[name="' + countfield + '"]');
  if (fieldval.length > maxlimit) {
      // if too long...trim it!
      jQuery(field).val(fieldval.substring(0, maxlimit));
      countfield.css('border', '1px solid red');
  }
  // update 'characters left' counter
  countfield.attr('value', Math.max(maxlimit - fieldval.length, 0));
}
