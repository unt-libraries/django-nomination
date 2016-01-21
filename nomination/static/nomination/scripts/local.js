// JavaScript Document

$(document).ready(function() {



	// Make Headings Toggle their next siblings (the field wrapper) visibility
	$('h2.collapse-next').next().hide().end().click(function() {
			$(this).toggleClass('closed').next().slideToggle();		
	});

	/*
	Handle the click events for add/remove fields.
	Take into account that some DOM elements will be newly inserted or created asyncronysily so take advantage of event bubbling.
	Assigning the functionality to the parent container to bind newly generated "remove" button
	Upon click of the button:
		clone
		change id and name attribute of divs, inputs, textareas, and selects by couting siblings and increasing value +1
		remove the add button
		append the remove button
		
		other handlers:
		
		handle check/uncheck all checkboxes
		copy GEO coordinates from google map to form field
		generate pre-filled inputs when users "Add" subject/keywords using the treeview plugin
		
	See: http://www.learningjquery.com/2008/03/working-with-events-part-1
	*/
	$('.field-wrapper').click(function(event) {
					var $tgt = $(event.target);		
					if ($tgt.is("a[href$='#select_all']")) {
						     $tgt.attr('href', '#select_none').text('Select None');
            			     $("." + $tgt.attr('rel') + " input[type='checkbox']").attr('checked', true);
            			     return false;
					}
					if ($tgt.is("a[href$='#select_none']")) {
  						     $tgt.attr('href', '#select_all').text('Select All');
           				     $("." + $tgt.attr('rel') + " input[type='checkbox']").attr('checked', false);
           				     return false;	
					}
					if ($tgt.is("a[href$='#add_subject_to_form']")) {
							var $subjectFormField = $('<input style="width:250px" disabled="disabled" type="text" name="subject-value" id="subject-value" value="" />')
														.appendTo('#subject .element-wrapper');

							$subjectFormField.each(function(index) {
									$(this).attr('id', 'subject-value-' +
											$(this)
											.siblings('input')
											.size());
									$(this).attr('name', 'subject-value-' +
											$(this)
											.siblings('input')
											.size())
								})
							 	.val($tgt.prev().text())
								.after('<a class="remove-from-form" href="#remove_subject_form_field">Remove</a>');
							 
           				     return false;	
					}
					if ($tgt.is("a[href$='#remove_subject_form_field']")) {
  						     $tgt.prev().remove();
   						     $tgt.remove();
           				     return false;	
					}
				});

        $('#preview-url').click(function() {
                                       // Get href from textbox
                                       window.open(document.getElementById('url-value').value, '_blank');
                                });
// browse List. http://plugins.jquery.com/project/treeview

// End Document Ready Function
});

function saveInformation() {
      // Save user information from the form!
      $.cookie('your-name-value', $("input[@id='your-name-value']").val(), { path: '/' });
      $.cookie('email-value', $("input[@id='email-value']").val(), { path: '/' });
      $.cookie('institution-value', $("input[@id='institution-value']").val(), { path: '/' });
   }
   
function getCookie(name) {
    var dc = document.cookie;
    var prefix = name + "=";
    var begin = dc.indexOf("; " + prefix);
    if (begin == -1) {
        begin = dc.indexOf(prefix);
        if (begin != 0) return null;
    } else {
        begin += 2;
    }
    var end = document.cookie.indexOf(";", begin);
    if (end == -1) {
        end = dc.length;
    }
    return unescape(dc.substring(begin + prefix.length, end));
}

function initForm() {
  $("#url-value").focus();
  // Autofill user information if available
  $("input[@id='your-name-value']").val(getCookie('your-name-value'));
  $("input[@id='email-value']").val(getCookie('email-value'));
  $("input[@id='institution-value']").val(getCookie('institution-value'));

  // Save comment information when form is submitted
  $("form").submit(saveInformation);
}
