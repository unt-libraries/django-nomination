var checkflag = false;

function checkAll(field) {
    var elements = document.getElementsByName(field);
    if (checkflag==false) {
        for (j=0; j<elements.length; j++) {
            if (elements[j].tagName=='INPUT' && elements[j].value!='other_specify') {
                elements[j].checked = true;
            }
        }
        checkflag = true;
        return "Deselect All";

    }

    else {
        for (j=0; j<elements.length; j++) {
            if (elements[j].tagName=='INPUT' && elements[j].value!='other_specify') {
                elements[j].checked = false;
            }
        }
        checkflag = false;
        return "Select All";

    }
}

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
