<!-- Original:  Ronnie T. Moore -->
<!-- Dynamic 'fix' by: Nannette Thacker -->

function textCounter(field, countfield, maxlimit) {

	if (field.value.length > maxlimit) {
	
		// if too long...trim it!
		field.value = field.value.substring(0, maxlimit);
		
        alert( 'This field is limited to ' + maxlimit + ' characters in length.' );
        		
	} else {
	
		// otherwise, update 'characters left' counter	
		countfield.value = maxlimit - field.value.length;
		
	}
}