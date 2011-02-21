// Keyword multiple select enhancement test - refs PLIP ticket #11017.
// The PLIP adds an accessible, jQuery-based widget, which includes both a scrollbar and checkboxes.

$(document).ready(function(){  

    $("#predefined_subjects").multiSelect();
    
    // These assignments are not used in the tests, 
    // but were handy for hovering variable names in Firebug when writing the tests, 
    // and could be handy for debugging failed tests if any failures happen in the future.
    multiple_select = $(".optionsBox");
    existing_tags = multiple_select.children();
    first_tag = existing_tags.first();
    first_label = $(".optionsBox label:first").text();
    first_selected = $("#selectedTags span:first").text();
    num_tags = existing_tags.length;
    checked_input_val = $(".optionsBox input:checked").val();
    checked_label = $(".optionsBox label.checked").css("backgroundColor");
	
    module("Tags multiple select enhancement test (refactored without anchor) - PLIP refs #11017");
	
    test("Handle selection of options test", function(){
		$(".optionsBox").selectionDevice = 'mouse';
		$(".optionsBox").selectionElement = $(".optionsBox label:first");
		$(".optionsBox").selectionOption = $(".optionsBox label:first");
        expect(1);
        equals( 
			$(".optionsBox label:first").hasClass('checked'),  
            false,  
            'Expected hasClass checked false as the result, result was: ' + $(".optionsBox label:first").hasClass('checked') 
		);  
		//mySelectOrDeselectAnOption.selectAnOption($(".optionsBox"));
//        equals( 
//			$(".optionsBox label:first").hasClass('checked'),  
//            true,  
//            'Expected hasClass checked true as the result, result was: ' + $(".optionsBox label:first").hasClass('checked') 
//		);  
    });
	
	// Now write tests as array of values, 
	// per http://www.adequatelygood.com/2010/7/Writing-Testable-JavaScript
	// First set includes label class, checkbox state, focus, focus with tab

	
    module("Tags multiple select enhancement test (still contains anchor) - PLIP refs #11017");  
    test("Div existence test", function(){  
        expect(1);  
        equals( $(".optionsBox").length,  
            1,  
            'Expected 1 optionsBox div as the result, result was: ' + $(".optionsBox").length );  
    });
    test("Tag dd count test", function(){  
        expect(1);  
        equals( $(".optionsBox").children().length,  
            16,  
            'Expected 16 as the result, result was: ' + $(".optionsBox").children().length );  
    });
    test("First label text test", function(){  
        expect(1);  
        equals( $(".optionsBox label:first").text(),  
            'An existing tag',  
            'Expected An existing tag as the result, result was: ' + $(".optionsBox label:first").text() );  
    });
    test("Pre-checked/selected text, checked, formatted, & listed test", function(){  
        expect(3);  
        equals( $(".optionsBox input:checked").val(),  
            "Major Initiatives: Nurture Community",  
            'Expected Major Initiatives: Nurture Community as the result, result was: ' + $(".optionsBox input:checked").val() );  
        equals( $(".optionsBox label.checked").css("backgroundColor"),  
            "rgb(238, 238, 238)",  
            'Expected rgb(238, 238, 238) as the result, result was: ' + $(".optionsBox label.checked").css("backgroundColor") );  
        equals( $("#selectedTags span:first").text(),  
            "Major Initiatives: Nurture Community",  
            'Expected Major Initiatives: Nurture Community as the result, result was: ' + $("#selectedTags span:first").text() );  
    });
    //test("Checkbox checked test", function(){  
        //expect(1);  
        //// This doesn't trigger the click methods in the js, not sure why.  
        //// That seems to wreck the possibility of testing this with QUnit; it currently fails.
        //$(".optionsBox input:first").click();  
        //ok( $(".optionsBox label:first").hasClass("hover"),  
            //'Expected hover class on first label.' );  
    //});
    
    // Other tests which would be nice:
    // Scrollbar present? - Can only test with qunit if moused down onto - inadequate.
    // Tab key nav- jQuery didn't catch it when I was working on the code; test doesn't appear possible.
    // Spacebar selection, formatting, and listing as currently selected tag.
    // Hover a middle tag, moving mouse in from the side, as a corner case.
    // Arrow key navigation.
    // Arrow key navigation div scrolling down properly.
});