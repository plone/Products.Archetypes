/*
// jQuery multiSelect
//
// Version 1.3
//
// Cory S.N. LaViska
// A Beautiful Site (http://abeautifulsite.net/)
// Visit http://abeautifulsite.net/notebook/62 for more information
//
// (Amended by Andy Richmond, Letters & Science Deans' Office, University of California, Davis)
//
// (Amended and trimmed for the Plone open source CMS by Matt Barkau, WebLion Group, PSU.edu)
//
// Usage: $('#control_id').multiSelect( arguments )
//
// Arguments:
//           noneSelected       - text to display when there are no selected items in the list
//           oneOrMoreSelected  - text to display when there are one or more selected items in the list
//                                (note: you can use % as a placeholder for the number of items selected).
//                                Use * to show a comma separated list of all selected; default = '% selected'
//
// Dependencies:  jQuery 1.2.6 or higher (http://jquery.com/)
//
// Change Log:
//
//		1.0.1	- Updated to work with jQuery 1.2.6+ (no longer requires the dimensions plugin)
//				- Changed $(this).offset() to $(this).position(), per James' and Jono's suggestions
//
//		1.0.2	- Fixed issue where dropdown doesn't scroll up/down with keyboard shortcuts
//				- Changed '$' in setTimeout to use 'jQuery' to support jQuery.noConflict
//				- Renamed from jqueryMultiSelect.* to jquery.multiSelect.* per the standard recommended at
//				  http://docs.jquery.com/Plugins/Authoring (does not affect API methods)
//
//		1.1.0	- Added the ability to update the options dynamically via javascript: multiSelectOptionsUpdate(JSON)
//              - Added a title that displays the whole comma delimited list when using oneOrMoreSelected = *
//              - Moved some of the functions to be closured to make them private
//              - Changed the way the keyboard navigation worked to more closely match how a standard dropdown works
//              - ** by Andy Richmond **
//
//		1.2.1	- Fixed bug where input text overlapped dropdown arrow in IE (i.e. when using oneOrMoreSelected = *)
//              - ** by Andy Richmond **
//
//		1.2.2	- 06 January 2010 (per http://abeautifulsite.net/blog/2008/04/jquery-multiselect )
//				- Fixed bug where the keypress stopped showing the dropdown because in jQuery 1.3.2 they changed the way ':visible' works
//              - Fixed some other bugs in the way the keyboard interface worked
//              - Changed the main textbox to an <a> tag (with 'display: inline-block') to prevent the display text from being selected/highlighted
//              - Added the ability to jump to an option by typing the first character of that option (simular to a normal drop down)
//              - ** by Andy Richmond **
//				- Added [] to make each control submit an HTML array so $.serialize() works properly
//
//		1.3		- 2010 October-November
//				- Adapted for Plone open source CMS tag selector
//				- Fixed bug related to mouse hover when using arrow keys
//				- Improved many areas of keyboard support & accessibility
//				- see https://dev.plone.org/archetypes/log/Products.Archetypes/branches/plip11017-tag-selector-rmattb/Products/Archetypes/skins/archetypes/widgets/js/keywordmultiselect.js
//				- ** by Matt Barkau **
//
// Licensing & Terms of Use
// 
// This plugin is dual-licensed under the GNU General Public License and the MIT License and
// is copyright 2008 A Beautiful Site, LLC. 
//	
*/

// Removed a test for jQuery, since we know it is available.
(function($){
	
	// render the html for a single option
	function renderOption(option, i, selectName)
	{
		// dl, dt, & dd semantically associates selector name with values
		// label makes the text clickable, like a multiple-select
		var html = '<dd><label for="tag' + i + '"><input type="checkbox" name="' + selectName + '" value="' + option.value + '" id="tag' + i + '"';
		if( option.selected ){
			html += ' checked="checked"';
		}
		html += ' />' + option.text + '</label></dd>';
		return html;
	}
	
	// render the html for the options/optgroups
	function renderOptions(options, selectName)
	{
		var html = "";
		for(var i = 0; i < options.length; i++) {
			html += renderOption(options[i], i, selectName);
		}
		return html;
	}
	
	// Building the actual options
	function buildOptions(options)
	{
		var multiSelectA = $(this);
		var multiSelectOptions = multiSelectA.next('.multiSelectOptions');
		
		// Help text here is only relevant when there are many tags, 
		// so putting that in documentation, rather than here.
		// "Hover and type the first letter to skip through tags."
		$("#existingTagsHelp").text('');

		// clear the existing options
		multiSelectOptions.html("");
		var html = "";

		// generate the html for the new options
		html += renderOptions(options, multiSelectOptions.attr('name'));
		
		multiSelectOptions.html(html);
		
		// Handle all checkboxes
		multiSelectOptions.find('INPUT:checkbox').click( function() {
			// set the label checked class
			$(this).parent('LABEL').toggleClass('checked', $(this).attr('checked'));
			
			updateSelected.call(multiSelectA);
			multiSelectA.focus();
			// If this checkbox was navigated to with the tab key before being checked, 
			// then put focus back on it.
			if(typeof(lastNavTabKeyCheckbox) != "undefined" && lastNavTabKeyCheckbox != null) {
				lastNavTabKeyCheckbox.focus();
				lastNavTabKeyCheckbox = null;
			}
		});
		
		// Initial display
		multiSelectOptions.each( function() {
			$(this).find('INPUT:checked').parent('LABEL').addClass('checked');
		});
		
		// Initialize selected
		updateSelected.call(multiSelectA);
		
		// Handle hovers (entering an option) *and* mouse moving within an option
		multiSelectOptions.find('LABEL').mousemove( function(e) {
			// Workaround Safari's errant reporting of mousemove when the mouse hasn't moved.
			// At this point, the browser is saying that the mouse moved.
			// Initialize position variables.
			if(multiSelectA.oldPositionX == null || multiSelectA.oldPositionY == null) {
				multiSelectA.oldPositionX = e.pageX;
				multiSelectA.oldPositionY = e.pageY;
			}
			if( multiSelectA.oldPositionX != e.pageX || multiSelectA.oldPositionY != e.pageY ) {
				// At this point, the mouse actually did move.  
				$(this).parent().parent().find('LABEL').removeClass('hover');
				$(this).addClass('hover');
				lastNavTabKeyCheckbox = null;
				multiSelectA.oldPositionX = e.pageX;
				multiSelectA.oldPositionY = e.pageY;
				multiSelectA.focus();
				adjustViewPort(multiSelectOptions);
			}
		});
		
		// Style checkbox parent with tab-driven focus
		multiSelectOptions.find('LABEL').mousedown(function(){
			// Track mouse clicks, 
			// so that tab key navigation focus on checkboxes can be maintained separately.
			lastNavClickTag = this;
		});
		multiSelectOptions.find('INPUT').focus(function(){
			if(typeof(lastNavClickTag) == "undefined" || lastNavClickTag == null) {
				// This only happens with tab key navgation.
				// Must keep track of this, because mouse-driven nav always keeps *focus* on multiSelectA, 
				// while the active multiSelectOptions get *hover*.
				// Tab navigation is different - it's active option checkbox gets *focus*, 
				// rather than *hover*, since keyboard navigation never hovers.
				// If the checkbox is tabbed to & checked , save it so that focus can be put back on it.
				// Without this, both moused & tabbed checks return focus to multiSelectA, 
				// causing tabbed checkboxes to lose focus.
				lastNavTabKeyCheckbox = $(this);
				// Remove hover class from all labels in the div
				lastNavTabKeyCheckbox.parent().parent().parent().find('LABEL').removeClass('hover');
				lastNavTabKeyCheckbox.parent('LABEL').addClass('hover');
			}
			lastNavClickTag = null;
		});
		
		// Keyboard
		multiSelectA.keydown( function(e) {
		
			var multiSelectOptions = $(this).next('.multiSelectOptions');
			
			// Down || Up
			if( e.keyCode == 40 || e.keyCode == 38) {
				var allOptions = multiSelectOptions.find('LABEL');
				var oldHoverIndex = allOptions.index(allOptions.filter('.hover'));
				var newHoverIndex = -1;
				
				// if there is no current highlighted item then highlight the first item
				if(oldHoverIndex < 0) {
					// Default to first item
					multiSelectOptions.find('LABEL:first').addClass('hover');
				}
				// else if we are moving down and there is a next item then move
				else if(e.keyCode == 40 && oldHoverIndex < allOptions.length - 1)
				{
					newHoverIndex = oldHoverIndex + 1;
				}
				// else if we are moving up and there is a prev item then move
				else if(e.keyCode == 38 && oldHoverIndex > 0)
				{
					newHoverIndex = oldHoverIndex - 1;
				}

				if(newHoverIndex >= 0) {
					$(allOptions.get(oldHoverIndex)).removeClass('hover'); // remove the current highlight
					$(allOptions.get(newHoverIndex)).addClass('hover'); // add the new highlight
					lastNavTabKeyCheckbox = null;
					
					// Adjust the viewport if necessary
					adjustViewPort(multiSelectOptions);
				}
				
				return false;
			}

			// Page up || Page down
			if( e.keyCode == 33 || e.keyCode == 34) {
				var allOptions = multiSelectOptions.find('LABEL');
				var oldHoverIndex = allOptions.index(allOptions.filter('.hover'));
				var newHoverIndex = -1;
				var optionsPerPage = 8;  // depends on css
				// if we are moving up and there is a prev item then move
				if(e.keyCode == 33 && oldHoverIndex > 0) {
					newHoverIndex = oldHoverIndex - optionsPerPage;
					if(newHoverIndex < 0) {
						newHoverIndex = 0;
					}
				}
				if(e.keyCode == 34 && oldHoverIndex < allOptions.length - 1) {
					newHoverIndex = oldHoverIndex + optionsPerPage;
					if(newHoverIndex > allOptions.length - 1) {
						newHoverIndex = allOptions.length - 1;
					}
				}
				$(allOptions).removeClass('hover'); // remove all highlights
				$(allOptions.get(newHoverIndex)).addClass('hover'); // add the new highlight
				lastNavTabKeyCheckbox = null;
				// Adjust the viewport if necessary
				adjustViewPort(multiSelectOptions);
				return false;
			}
				
			// Enter, Space
			if( e.keyCode == 13 || e.keyCode == 32 ) {
				var selectedCheckbox = multiSelectOptions.find('LABEL.hover INPUT:checkbox');
				
				// Set the checkbox (and label class)
				selectedCheckbox.attr('checked', !selectedCheckbox.attr('checked')).parent('LABEL').toggleClass('checked', selectedCheckbox.attr('checked'));
				
				updateSelected.call(multiSelectA);
				return false;
			}

			// Any other standard keyboard character (try and match the first character of an option)
			if( e.keyCode >= 33 && e.keyCode <= 126 ) {
				// find the next matching item after the current hovered item
				var match = multiSelectOptions.find('LABEL:startsWith(' + String.fromCharCode(e.keyCode) + ')');
				
				var currentHoverIndex = match.index(match.filter('LABEL.hover'));
				
				// filter the set to any items after the current hovered item
				var afterHoverMatch = match.filter(function (index) {
					return index > currentHoverIndex;
				});

				// if there were no item after the current hovered item then try using the full search results (filtered to the first one)
				match = (afterHoverMatch.length >= 1 ? afterHoverMatch : match).filter("LABEL:first");

				if(match.length == 1) {
					// if we found a match then move the hover
					multiSelectOptions.find('LABEL.hover').removeClass('hover');
					match.addClass('hover');
					lastNavTabKeyCheckbox = null;
					
					adjustViewPort(multiSelectOptions);
				}
			}
			// Prevent enter key from submitting form
			if( e.keyCode == 13 ) return false;
		});
	}
	
	// Scroll the viewport div if necessary
	function adjustViewPort(multiSelectOptions)
	{
		// check for and move scrollbar down, content up
		var hoverTop = multiSelectOptions.find('LABEL.hover').position().top;
		var hoverHeight = multiSelectOptions.find('LABEL.hover').outerHeight();
		var selectionBottom = hoverTop + hoverHeight;
		// The integer 18 is a manual approximation for typical scale, 
		// since there's extra padding at the top of the div.multiSelectOptions
		// which is not showing up anywhere quantitatively. 
		// Could use improvement.
		var optionsHeight = multiSelectOptions.outerHeight() + 18;
		var optionsScrollTop = multiSelectOptions.scrollTop();
		if(selectionBottom > optionsHeight){		
			multiSelectOptions.scrollTop(optionsScrollTop + selectionBottom - optionsHeight);
		}
		
		// check for and move scrollbar up, content down
		var hoveredTop = multiSelectOptions.find('LABEL.hover').position().top;
		var optionsTop = multiSelectOptions.position().top;
		var optionsScrollTop = multiSelectOptions.scrollTop();
		if(hoveredTop < optionsTop){		
			multiSelectOptions.scrollTop(optionsScrollTop + hoveredTop - optionsTop);
		}
	}
	
	// Update heading with the total number of selected items
	function updateSelected() {
		var multiSelectA = $(this);
		var multiSelectOptions = multiSelectA.next('.multiSelectOptions');
		var o = multiSelectA.data("config");
		var i = 0;
		var display = '';
		multiSelectOptions.find('INPUT:checkbox').not('.selectAll, .optGroup').each( function() {
			if( $(this).attr('checked') ) {
				i++;
				display = 
					display + 
					'<p class="selectedTag"><span class="selectedTag">' + 
					$(this).parent().text() + 
					'</span></p>';
			}
			else selectAll = false;
		});
		
		if( i == 0 ) {
			$("#selectedTagsHeading").html( $("#noTagsSelected").text() );
			$("#selectedTags").text('');
		} else {
			$("#selectedTags").html( display )
			$("#selectedTagsHeading").html( $("#oneOrMoreTagsSelected").text().replace('%', i) );
		}
	}
	
	$.extend($.fn, {
		multiSelect: function(o) {

			// Initialize each multiSelectA
			$(this).each( function() {
				var select = $(this);
				// anchor originally used for dropdown
				var html = '<a href="javascript:;" class="multiSelectA" tabindex="1"><span></span></a>';
				// overflow-y: auto enables the scrollbar, like a multiple-select
				html += '<div class="multiSelectOptions" tabindex="9999" style="overflow-y: auto;"></div>';
				// display:block makes the blank area right of the text clickable, like a multiple-select
				html += '<style type="text/css">label {display: block;}</style>';
				$(select).after(html);
				
				var multiSelectA = $(select).next('.multiSelectA');
				var multiSelectOptions = multiSelectA.next('.multiSelectOptions');
				
				// Serialize the select options into json options
				var options = [];
				$(select).children().each( function() {
					if( $(this).val() != '' ) {
						options.push({ text: $(this).html(), value: $(this).val(), selected: $(this).attr('selected') });
					}
				});
				
				// Eliminate the original form element
				$(select).remove();
				
				// Add the id & name that was on the original select element to the new div
				multiSelectOptions.attr("id", $(select).attr("id"));
				multiSelectOptions.attr("name", $(select).attr("name"));
				
				// Build the dropdown options
				buildOptions.call(multiSelectA, options);
			
			});
		}
		
	});
	
	// add a new ":startsWith" search filter
	$.expr[":"].startsWith = function(el, i, m) {
		var search = m[3];        
		if (!search) return false;
		return eval("/^[/s]*" + search + "/i").test($(el).text());
	};
	
})(jQuery);