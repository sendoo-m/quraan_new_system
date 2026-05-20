from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Student, AgeGroup
from .resources import StudentResource


@admin.register(AgeGroup)
class AgeGroupAdmin(ImportExportModelAdmin):
    list_display  = ('name', 'min_age', 'max_age', 'order', 'is_active')
    list_editable = ('min_age', 'max_age', 'order', 'is_active')
    ordering      = ('order', 'min_age')


@admin.register(Student)
class StudentAdmin(ImportExportModelAdmin):
    resource_class    = StudentResource
    list_display      = (
        'get_full_name', 'calculate_age', 'age_group',
        'parent', 'hall', 'status', 'uses_bus', 'registration_date'
    )
    list_filter       = ('status', 'age_group', 'uses_bus', 'hall')
    search_fields     = ('first_name', 'last_name', 'parent__username')
    filter_horizontal = ('memorized_surahs',)
    readonly_fields   = ('registration_date', 'age_group')

    fieldsets = (
        ('البيانات الأساسية', {
            'fields': (
                'first_name', 'last_name', 'date_of_birth',
                'emergency_phone', 'age_group',
            )
        }),
        ('القرآن الكريم', {
            'fields': ('memorized_surahs',)
        }),
        ('التسجيل', {
            'fields': ('parent', 'hall', 'status', 'uses_bus', 'bus_notes', 'notes')
        }),
    )