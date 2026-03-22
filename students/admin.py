from django.contrib import admin
from .models import Student, AgeGroup


@admin.register(AgeGroup)
class AgeGroupAdmin(admin.ModelAdmin):
    list_display  = ('name', 'min_age', 'max_age', 'order', 'is_active')
    list_editable = ('min_age', 'max_age', 'order', 'is_active')
    ordering      = ('order', 'min_age')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
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
            'fields': ('first_name', 'last_name', 'date_of_birth',
                       'age_group', 'profile_picture')
        }),
        ('القرآن الكريم', {
            'fields': ('memorized_surahs',)
        }),
        ('التسجيل', {
            'fields': ('parent', 'hall', 'status', 'uses_bus', 'bus_notes', 'notes')
        }),
    )

# from django.contrib import admin
# from .models import Student


# @admin.register(Student)
# class StudentAdmin(admin.ModelAdmin):
#     list_display  = (
#         'get_full_name', 'calculate_age', 'age_group',
#         'parent', 'hall', 'status', 'uses_bus', 'registration_date'
#     )
#     list_filter   = ('status', 'age_group', 'uses_bus', 'hall')
#     search_fields = ('first_name', 'last_name', 'parent__username')
#     filter_horizontal = ('memorized_surahs',)
#     readonly_fields   = ('registration_date', 'age_group')

#     fieldsets = (
#         ('البيانات الأساسية', {
#             'fields': ('first_name', 'last_name', 'date_of_birth',
#                        'age_group', 'profile_picture')
#         }),
#         ('القرآن الكريم', {
#             'fields': ('memorized_surahs',)
#         }),
#         ('التسجيل', {
#             'fields': ('parent', 'hall', 'status', 'uses_bus', 'bus_notes', 'notes')
#         }),
#     )
