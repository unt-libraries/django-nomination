from django.contrib import admin
from django import forms
from nomination.models import (Project, Project_Metadata, Metadata_Values,
                               Valueset_Values, Nominator, URL, Metadata,
                               Value, ValueSet)


class ProjectMetadataInline(admin.TabularInline):
    model = Project_Metadata
    extra = 3


class ProjectAdmin(admin.ModelAdmin):
    """ Project class that determines how comment appears in admin """
    list_display = ('project_slug', 'project_name', 'project_active', 'nomination_active')
    inlines = [ProjectMetadataInline]
    ordering = ('project_slug',)


class NominatorAdmin(admin.ModelAdmin):
    """ Nominator class that determines how comment appears in admin """
    list_display = ('nominator_name', 'nominator_email', 'nominator_institution', 'nominations')
    list_display_links = ('nominator_name',)
    ordering = ('nominator_name',)


class URLAdmin(admin.ModelAdmin):
    """ URL class that determines how comment appears in admin """
    list_display = ('get_project', 'get_nominator', 'entity_display', 'attribute', 'value', 'date')
    list_filter = ('url_project', 'url_nominator', 'attribute', 'date',)
    search_fields = ('entity', 'attribute', 'value',)
    list_display_links = ('attribute', 'value',)
    ordering = ('entity', 'attribute',)
    date_hierarchy = 'date'


class ProjectAdminForm(forms.ModelForm):
    """ Project class to specify how form data is handled in admin """

    class Meta:
        model = Project
        fields = '__all__'

    def clean_project_slug(self):
        """ Make sure the project_slug field is alphanumeric """
        if self.cleaned_data["project_slug"].isalnum():
            return self.cleaned_data["project_slug"]
        else:
            raise forms.ValidationError("The project slug must be alphanumeric.")


class MetadataValuesInline(admin.TabularInline):
    model = Metadata_Values
    extra = 10


class MetadataAdmin(admin.ModelAdmin):
    list_display = ('name',)
#    list_display = ('name', 'project', 'form_type', 'description', 'metadata_order', 'required')
    inlines = [MetadataValuesInline]
    search_fields = ['name']
#    list_filter = ('project', 'name', 'form_type', 'required')


class ValueAdmin(admin.ModelAdmin):
    list_display = ('value', 'key',)
    search_fields = ['value', 'key']


class ValuesetValuesInline(admin.TabularInline):
    model = Valueset_Values
    extra = 5


class ValueSetAdmin(admin.ModelAdmin):
    list_display = ('name',)
    inlines = [ValuesetValuesInline]
#    search_fields = ('name',)
#    ordering = ('name',)
#    filtering_horizontal = ('elements',)


admin.site.register(Project, ProjectAdmin)
admin.site.register(Nominator, NominatorAdmin)
admin.site.register(URL, URLAdmin)
admin.site.register(Metadata, MetadataAdmin)
admin.site.register(Value, ValueAdmin)
admin.site.register(ValueSet, ValueSetAdmin)
