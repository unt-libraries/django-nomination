from nomination.models import Project, URL, Value
import itertools
from django import forms
import copy

type_mapping = {
    'CharField': forms.CharField(max_length = 255),
    'TextField': forms.CharField(widget = forms.Textarea),
    'BooleanField': forms.BooleanField(required = False),
    'URLField': forms.URLField(),
    'EmailField': forms.EmailField(),
    'ChoiceField': forms.ChoiceField(choices=[('temp', 'Temp'),]),
    'DateField': forms.DateTimeField(),
    'URLField': forms.URLField(),
    }

form_map = {
    'checkbox': ('ChoiceField', 'CheckboxSelectMultiple'),
    'radio': ('ChoiceField', 'RadioSelect'),
    'selectsingle': ('ChoiceField', 'Select'),
    'select': ('ChoiceField', 'SelectMultiple'),
    'text': ('CharField', 'TextInput'),
    'textarea': ('TextField', 'Textarea'), 
    'date': ('DateField', 'DateInput'),
    }

widget_map = {
    'CheckboxSelectMultiple': forms.CheckboxSelectMultiple(),
#    'DateInput': forms.DateInput(),
    'DateInput': forms.DateTimeInput(),
    'DateTimeInput': forms.DateTimeInput(),
    'RadioSelect': forms.RadioSelect(),
    'Select': forms.Select(),
    'SelectMultiple': forms.SelectMultiple(),
    'Textarea': forms.Textarea(),
    'TextInput': forms.TextInput(),
    }

def make_metadata_form(project):
    """Returns a form for metadata input."""
    metadata_fields = project.project_metadata_set.all().order_by('metadata_order')

    class MetadataForm(forms.Form):
        def __init__(self):
            forms.Form.__init__(self)

    # create form fields
    mformclass = type('MetadataForm', (forms.Form,), dict(MetadataForm.__dict__))
    for field in metadata_fields:
#        setattr(MetadataForm, field.metadata.name, copy.copy(type_mapping[form_map[field.form_type][0]]))
        mformclass.base_fields[field.metadata.name] =  copy.copy(type_mapping[form_map[field.form_type][0]])
    # set field attributes and  widgets
    for k, v in mformclass.base_fields.items():
        field = metadata_fields.get(metadata__name=k)
        v.widget = widget_map[form_map[field.form_type][1]]
        v.widget.attrs =  {'name' : field.metadata.name, 'id' : field.metadata.name,}
        v.required = False | field.required
        v.help_text = field.help
        v.label = field.description
        if field.form_type not in ('text', 'textarea', 'date'):
            choicelist = get_all_vals(field.metadata)
            if choicelist:
                v.choices = choicelist
            print v.choices
        if field.form_type in ('text', 'textarea', 'date') and \
          len(field.metadata.values.all()) >= 1:
            v.initial = field.metadata.values.all()[0]
         
            print 'initial ', v.initial
        print v.widget
        print v.widget.attrs
        print v.label
        print v.help_text
        print '\n'
    return mformclass

def get_all_vals(mobj):
    """Combines values from value_sets and individual values.

    mobj is a metadata object.
    """
    ordered_vals = []
    all_vals = mobj.values.all().order_by('metadata_values')
    val_sets = mobj.value_sets.all()
    for z in val_sets:
        all_vals = itertools.chain(z.values.all().order_by('valueset_values'), all_vals)
    for each in all_vals:
        ordered_vals.append((each.key, each.value))
    return ordered_vals

