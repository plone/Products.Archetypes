// Keyword multiple select enhancement test - refs PLIP ticket #11017.
// The PLIP adds an accessible, jQuery-based widget, which includes both a scrollbar and checkboxes.

$(document).ready(function(){  

    $("#predefined_subjects").multiSelect();
    
    // These assignments are not used in the tests, 
    // but were handy for hovering variable names in Firebug when writing the tests, 
    // and could be handy for debugging failed tests if any failures happen in the future.
    multiple_select = $(".multiSelectOptions");
    existing_tags = multiple_select.children();
    first_tag = existing_tags.first();
    first_label = $(".multiSelectOptions label:first").text();
    first_selected = $("#selectedTags span:first").text();
    num_tags = existing_tags.length;
    checked_input_val = $(".multiSelectOptions input:checked").val();
    checked_label = $(".multiSelectOptions label.checked").css("backgroundColor");

    module("Keyword multiple select enhancement test - refs PLIP ticket #11017");  
    test("Div existence test", function(){  
        expect(1);  
        equals( $(".multiSelectOptions").length,  
            1,  
            'Expected 1 as the result, result was: ' + $(".multiSelectOptions").length );  
    });
    test("Tag dd count test", function(){  
        expect(1);  
        equals( $(".multiSelectOptions").children().length,  
            16,  
            'Expected 16 as the result, result was: ' + $(".multiSelectOptions").children().length );  
    });
    test("First label text test", function(){  
        expect(1);  
        equals( $(".multiSelectOptions label:first").text(),  
            'An existing tag',  
            'Expected An existing tag as the result, result was: ' + $(".multiSelectOptions label:first").text() );  
    });
    test("Pre-checked/selected text, checked, formatted, & listed test", function(){  
        expect(3);  
        equals( $(".multiSelectOptions input:checked").val(),  
            "Major Initiatives: Nurture Community",  
            'Expected Major Initiatives: Nurture Community as the result, result was: ' + $(".multiSelectOptions input:checked").val() );  
        equals( $(".multiSelectOptions label.checked").css("backgroundColor"),  
            "rgb(238, 238, 238)",  
            'Expected rgb(238, 238, 238) as the result, result was: ' + $(".multiSelectOptions label.checked").css("backgroundColor") );  
        equals( $("#selectedTags span:first").text(),  
            "Major Initiatives: Nurture Community",  
            'Expected Major Initiatives: Nurture Community as the result, result was: ' + $("#selectedTags span:first").text() );  
    });
    //test("Checkbox checked test", function(){  
        //expect(1);  
        //// This doesn't trigger the click methods in the js, not sure why.  
        //// That seems to wreck the possibility of testing this with QUnit; it currently fails.
        //$(".multiSelectOptions input:first").click();  
        //ok( $(".multiSelectOptions label:first").hasClass("hover"),  
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