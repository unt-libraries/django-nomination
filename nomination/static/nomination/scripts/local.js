/*
 * Functions for autofilling form data within a session
 */

function saveInformation() {
    // Save user information from the form in session cookies
    Cookies.set('your-name-value', $("input[id='your-name-value']").val());
    Cookies.set('email-value', $("input[id='email-value']").val());
    Cookies.set('institution-value', $("input[id='institution-value']").val());
}

function retrieveInformation() {
    // Set form values to information retrieved from cookies
    $("input[id='your-name-value']").val(Cookies.get('your-name-value'));
    $("input[id='email-value']").val(Cookies.get('email-value'));
    $("input[id='institution-value']").val(Cookies.get('institution-value'));
}

function focusAddForm() {
    // Focus on URL field after placeholder text
    var $urlValue = $('#url-value').get(0);
    var urlValueLen = $urlValue.value.length;
    $urlValue.selectionStart = urlValueLen;
    $urlValue.selectionEnd = urlValueLen;
    $urlValue.focus();
}

function initForm() {
    // Autofill user information if available
    retrieveInformation();
    bindSelectAll();

    // Save comment information when form is submitted
    $("form").submit(saveInformation);
}

// Toggle for check/uncheck all
function bindSelectAll() {
    $('input[data-check-all="true"]').on('click', function() {

        // Select all checkbox siblings of button, except "other"
        var $checkboxes = $(this).siblings('.checkbox')
                                 .find('input[type="checkbox"]')
                                 .not('[value="other_specify"]');

        // Use data field to determine check state
        if( $(this).data('check-state') === 'select' ) {
            $checkboxes.each(function() {
                $(this).prop('checked', true);
            });
            $(this).attr('value', 'Deselect All').data('check-state', 'deselect');
        } else {
            $checkboxes.each(function() {
                $(this).prop('checked', false);
            });
            $(this).attr('value', 'Select All').data('check-state', 'select');
        }
    });
}

// Launch URL in new window
function bindPreviewURL() {
    $('#previewUrl').on('click', function(e) {
        e.preventDefault();
        e.stopPropagation();
        var newUrl = $('#url-value').val();

        if( newUrl === 'http://' || newUrl === 'https://' ) {
            $('#invalidUrlError').removeClass('hidden');
        } else {
            $('#invalidUrlError').addClass('hidden');
            window.open(newUrl, '_blank');
        }
    });
}

// Use json_data in template to repopulate a form after form errors
function repopulateForm() {
    for (j=0; j<json_data.length; j++) {
        if (json_data[j][1].length == 1 && json_data[j][1][0] == "") {
            continue;
        }
        else {
            ft = form_types[json_data[j][0]];
            if (ft != undefined) {
                if (ft == 'select' || ft == 'selectsingle') {
                    for (k=0; k<json_data[j][1].length; k++) {
                        for (m=0; m<document.getElementById(json_data[j][0]).options.length; m++) {
                            if (document.getElementById(json_data[j][0]).options[m].value != json_data[j][1][k]) {
                                continue;
                            }
                            else {
                                document.getElementById(json_data[j][0]).options[m].selected = true;
                            }
                        }
                    }
                }
                else if (ft == 'text' || ft == 'textarea' || ft == 'date') {
                    document.getElementById(json_data[j][0]).value = json_data[j][1][0];
                }
                else if (ft == 'checkbox' || ft == 'radio') {
                    for (k=0; k<json_data[j][1].length; k++) {
                        for (m=0; m<document.getElementsByName(json_data[j][0]).length; m++) {
                            if (document.getElementsByName(json_data[j][0])[m].value != json_data[j][1][k]) {
                                continue;
                            }
                            else {
                                document.getElementsByName(json_data[j][0])[m].checked = true;
                            }
                        }
                    }
                }
            }
            else {
                // undefined case: do stuff for default fields
                if (json_data[j][0] == 'url_value') {
                    document.getElementById('url-value').value = json_data[j][1][0];
                }
                // handle user specified text fields (other_specify types)
                else if (json_data[j][0].match(/^.*_other$/)) {
                    document.getElementById(json_data[j][0]).value = json_data[j][1][0];
                }
            }
        }
    }
}
