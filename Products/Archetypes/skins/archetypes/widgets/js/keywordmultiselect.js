/*jslint white:false, onevar:true, undef:true, nomen:true, eqeqeq:true, plusplus:true, bitwise:true, regexp:true, newcap:true, immed:true, strict:false, browser:true */
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
//		1.1.0	- Added the ability to update the options dynamically via javascript: optionsBoxUpdate(JSON)
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
(function($) {

	// render the html for a single option
	function renderOption(option, i, selectName) {
		// dl, dt, & dd semantically associates selector name with values
		// label makes the text clickable, like a multiple-select
		var html = '<dd><label for="tag' + i + '"><input type="checkbox" name="' + selectName + '" value="' + option.value + '" id="tag' + i + '"';
		if( option.selected ) {
			html += ' checked="checked"';
		}
		html += ' />' + option.text + '</label></dd>';
		return html;
	}

	// render the html for the options/optgroups
	function renderOptions(options, selectName) {
		var html = "";
		for(var i = 0; i < options.length; i++) {
			html += renderOption(options[i], i, selectName);
		}
		return html;
	}


//  Plans to later modularize input and output handling,
//  for better testability, modularity, and accessibility.
//	// Handle mouse move input
//	// Handle mouse click input
//	// Handle key press input
//	// Detect navigation with mouse or non-tab keys
//	// Detect navigation with tab key
//	// Detect selection with mouse
//	// Detect selection with keyboard
//	// Handle navigation of options
//	// Handle selection of options


	// Building the actual options
	function buildOptions(options) {
		var optionsBox = $(this);
		var multiSelectA = optionsBox.next('.multiSelectA');

		// Help text here is only relevant when there are many tags,
		// so putting that in documentation, rather than here.
		// "Hover and type the first letter to skip through tags."
		$("#existingTagsHelp").text('');

		// generate the html for the new options
		html = renderOptions(options, optionsBox.attr('name'));
		optionsBox.html(html);

		// Format selected options
		optionsBox.each( function() {
			$(this).find('INPUT:checked').parent('LABEL').addClass('checked');
		});

		// Initialize selected options list
		updateSelected.call(optionsBox);
		var allOptions = optionsBox.find('LABEL');

		// --- Navigation with Mouse ---
		// Handle mouse hover of option, both
		// entering an option, *and*
		// mouse moving within an option.
		optionsBox.find('LABEL').mousemove( function(e) {
			// At this point, the browser is saying that the mouse moved.
			// Workaround Safari's errant reporting of mousemove
			// when the mouse hasn't moved, but background has.
			// Initialize position variables.
			if(multiSelectA.oldPositionX === null || multiSelectA.oldPositionY === null) {
				multiSelectA.oldPositionX = e.pageX;
				multiSelectA.oldPositionY = e.pageY;
			}
			if( multiSelectA.oldPositionX != e.pageX || multiSelectA.oldPositionY != e.pageY ) {
				// At this point, the mouse actually did move.
				// Highlight navigated option
				$(this).parent().parent().find('LABEL').removeClass('hover'); // remove all highlights
				$(this).addClass('hover'); // add the new highlight
				lastNavTabKeyCheckbox = null;
				multiSelectA.oldPositionX = e.pageX;
				multiSelectA.oldPositionY = e.pageY;
				multiSelectA.focus();
				adjustViewPort(optionsBox);
			}
		});

		// --- Selection with Mouse ---
		// Handle mouse click of checkbox
		optionsBox.find('INPUT:checkbox').click( function() {
			// set the label checked class
			$(this).parent('LABEL').toggleClass('checked', $(this).attr('checked'));

			updateSelected.call(optionsBox);
			// Highlight selected option
			// placeholder
			// Refocus
			multiSelectA.focus();
			// If this checkbox was navigated to with the tab key before being checked,
			// then put focus back on it.
			if(typeof(lastNavTabKeyCheckbox) !== "undefined" && lastNavTabKeyCheckbox !== null) {
				lastNavTabKeyCheckbox.focus();
				lastNavTabKeyCheckbox = null;
			}
		});

		// --- Navigation with Tab Key ---
		// Track mouse click of option
		optionsBox.find('LABEL').mousedown(function() {
			// Track mouse clicks,
			// so that tab key navigation focus on checkboxes can be maintained separately.
			lastNavClickTag = this;
		});
		// Handle tab-key focus of checkbox
		optionsBox.find('INPUT').focus(function() {
			if(typeof(lastNavClickTag) == "undefined" || lastNavClickTag === null) {
				// This only happens with tab key navgation.
				// Must keep track of this, because
				// mouse-driven nav always keeps *focus* on multiSelectA,
				// while the active optionsBox get *hover*.
				// Tab navigation is different - it's active option checkbox gets *focus*,
				// rather than *hover*, since keyboard navigation never hovers.
				// If the checkbox is tabbed to & checked , save it so that focus can be put back on it.
				// Without this, both moused & tabbed checks return focus to multiSelectA,
				// causing tabbed checkboxes to lose focus.
				lastNavTabKeyCheckbox = $(this);
				// Highlight navigated option
				lastNavTabKeyCheckbox.parent().parent().parent().find('LABEL').removeClass('hover');
				lastNavTabKeyCheckbox.parent('LABEL').addClass('hover');
			}
			lastNavClickTag = null;
		});

		// Handle keyboard press
		multiSelectA.keydown( function(e) {

			var optionsBox = $(this).prev('.optionsBox');

			// --- Navigation with Arrow or Page Keys ---
			// Down || Up
			if( e.keyCode == 40 || e.keyCode == 38) {
				var oldHoverIndex = allOptions.index(allOptions.filter('.hover'));
				var newHoverIndex = -1;

				// if there is no current highlighted item then highlight the first item
				if(oldHoverIndex < 0) {
					// Default to first item
					optionsBox.find('LABEL:first').addClass('hover');
				}
				// else if we are moving down and there is a next item then move
				else if(e.keyCode == 40 && oldHoverIndex < allOptions.length - 1) {
					newHoverIndex = oldHoverIndex + 1;
				}
				// else if we are moving up and there is a prev item then move
				else if(e.keyCode == 38 && oldHoverIndex > 0) {
					newHoverIndex = oldHoverIndex - 1;
				}

				if(newHoverIndex >= 0) {
					// Highlight navigated option
					$(allOptions).removeClass('hover'); // remove old highlights
					$(allOptions.get(newHoverIndex)).addClass('hover'); // add the new highlight
					lastNavTabKeyCheckbox = null;

					// Adjust the viewport if necessary
					adjustViewPort(optionsBox);
				}

				return false;
			}
			// Page up || Page down
			if( e.keyCode == 33 || e.keyCode == 34) {
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
				// Highlight navigated option
				$(allOptions).removeClass('hover'); // remove all highlights
				$(allOptions.get(newHoverIndex)).addClass('hover'); // add the new highlight
				lastNavTabKeyCheckbox = null;
				// Adjust the viewport if necessary
				adjustViewPort(optionsBox);
				return false;
			}

			// --- Selection with Keyboard ---
			// Enter, Space
			if( e.keyCode == 13 || e.keyCode == 32 ) {
				var selectedCheckbox = optionsBox.find('LABEL.hover INPUT:checkbox');
				// Set the checkbox (and label class)
				selectedCheckbox.attr('checked', !selectedCheckbox.attr('checked')).parent('LABEL').toggleClass('checked', selectedCheckbox.attr('checked'));
				// Highlight selected option
				// placeholder
				// Refocus
				// placeholder
				updateSelected.call(optionsBox);
				return false;
			}

			// Any other standard keyboard character (try and match the first character of an option)
			if( e.keyCode >= 33 && e.keyCode <= 126 ) {
				// find the next matching item after the current hovered item
				var match = optionsBox.find('LABEL:startsWith(' + String.fromCharCode(e.keyCode) + ')');

				var currentHoverIndex = match.index(match.filter('LABEL.hover'));

				// filter the set to any items after the current hovered item
				var afterHoverMatch = match.filter(function (index) {
					return index > currentHoverIndex;
				});

				// if there were no item after the current hovered item then try using the full search results (filtered to the first one)
				match = (afterHoverMatch.length >= 1 ? afterHoverMatch : match).filter("LABEL:first");

				if(match.length == 1) {
					// if we found a match then move the hover
					// Highlight navigated option
					$(allOptions).removeClass('hover'); // remove all highlights
					match.addClass('hover'); // add the new highlight
					lastNavTabKeyCheckbox = null;

					adjustViewPort(optionsBox);
				}
			}
			// Prevent enter key from submitting form
			if (e.keyCode == 13) {
				return false;
			}
		});
	}

	// Scroll the viewport div if necessary
	function adjustViewPort(optionsBox) {
		// check for and move scrollbar down, content up
		var hoverTop = optionsBox.find('LABEL.hover').position().top;
		var hoverHeight = optionsBox.find('LABEL.hover').outerHeight();
		var selectionBottom = hoverTop + hoverHeight;
		// The integer 18 is a manual approximation for typical scale,
		// since there's extra padding at the top of the div.optionsBox
		// which is not showing up anywhere quantitatively.
		// Could use improvement.
		var optionsHeight = optionsBox.outerHeight() + 18;
		var optionsScrollTop = optionsBox.scrollTop();
		if(selectionBottom > optionsHeight) {
			optionsBox.scrollTop(optionsScrollTop + selectionBottom - optionsHeight);
		}

		// check for and move scrollbar up, content down
		var hoveredTop = optionsBox.find('LABEL.hover').position().top;
		var optionsTop = optionsBox.position().top;
		optionsScrollTop = optionsBox.scrollTop();
		if(hoveredTop < optionsTop) {
			optionsBox.scrollTop(optionsScrollTop + hoveredTop - optionsTop);
		}
	}

	// Update heading with the total number of selected items
	function updateSelected() {
		var optionsBox = $(this);
		var multiSelectA = optionsBox.next('.multiSelectA');
		var i = 0;
		var display = '';
		optionsBox.find('INPUT:checkbox').not('.selectAll, .optGroup').each( function() {
			if ($(this).attr('checked')) {
				i++;
				display = display +
				'<p class="selectedTag"><span class="selectedTag">' +
				$(this).parent().text() +
				'</span></p>';
			}
			else {
				selectAll = false;
			}
		});

		if( i === 0 ) {
			$("#selectedTagsHeading").html( $("#noTagsSelected").text() );
			$("#selectedTags").text('');
		} else {
			$("#selectedTags").html( display );
			$("#selectedTagsHeading").html( $("#oneOrMoreTagsSelected").text().replace('%', i) );
		}
	}

	$.extend($.fn, {
		multiSelect: function() {

			// Initialize each optionsBox
			$(this).each( function() {
				var select = $(this);
				var html = '';
				// Overflow-y: auto enables the scrollbar, like a multiple-select
				html += '<div class="optionsBox" tabindex="9999" style="overflow-y: auto;"></div>';
				// Anchor originally used for dropdown.
				// Will try to remove after refactoring to be more modular and testable with QUnit,
				// although this element may need to stay to hold focus for mouse & arrow key navigation.
				html += '<a href="javascript:;" class="multiSelectA" title="enable tag selector: tag selector is currently enabled"></a>';
				// display:block makes the blank area right of the text clickable, like a multiple-select
				html += '<style type="text/css">.ArchetypesKeywordWidget label {display: block;}</style>';
				$(select).after(html);

				var optionsBox = $(select).next('.optionsBox');
				var multiSelectA = optionsBox.next('.multiSelectA');

				// Serialize the select options into json options
				var options = [];
				$(select).children().each( function() {
					if( $(this).val() !== '' ) {
						options.push({ text: $(this).html(), value: $(this).val(), selected: $(this).attr('selected') });
					}
				});

				// Eliminate the original form element
				$(select).remove();

				// Add the id & name that was on the original select element to the new div
				optionsBox.attr("id", $(select).attr("id"));
				optionsBox.attr("name", $(select).attr("name"));

				// Build the dropdown options
				buildOptions.call(optionsBox, options);

			});
		}

	});

	// add a new ":startsWith" search filter
	$.expr[":"].startsWith = function(el, i, m) {
		var search = m[3];
		if (!search) {
			return false;
		}
		return eval("/^[/s]*" + search + "/i").test($(el).text());
	};

})(jQuery);
