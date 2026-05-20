from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Hall, Subject, HallSchedule, ScheduleTemplate, ScheduleTemplateEntry
from .resources import HallResource, SubjectResource, ScheduleTemplateResource


@admin.register(Hall)
class HallAdmin(ImportExportModelAdmin):
    resource_class = HallResource
    list_display   = (
        'name',
        'age_group',
        'general_supervisor',
        'teacher',
        'supervisor',
        'get_current_students_count',
        'max_students',
        'required_completed_juz_count',
        'current_juz',
        'is_active',
    )
    list_filter   = ('is_active', 'age_group', 'general_supervisor')
    search_fields = ('name', 'location')


@admin.register(Subject)
class SubjectAdmin(ImportExportModelAdmin):
    resource_class = SubjectResource
    list_display   = ('name', 'is_active')
    search_fields  = ('name',)


@admin.register(HallSchedule)
class HallScheduleAdmin(admin.ModelAdmin):
    list_display  = ('hall', 'subject', 'day', 'start_time', 'end_time')
    list_filter   = ('hall', 'day')
    search_fields = ('hall__name', 'subject__name')


@admin.register(ScheduleTemplate)
class ScheduleTemplateAdmin(ImportExportModelAdmin):
    resource_class = ScheduleTemplateResource
    list_display   = ('name', 'is_active', 'get_halls_count', 'get_entries_count')
    search_fields  = ('name',)


@admin.register(ScheduleTemplateEntry)
class ScheduleTemplateEntryAdmin(admin.ModelAdmin):
    list_display  = ('template', 'subject', 'day', 'start_time', 'end_time')
    list_filter   = ('template', 'day')
    search_fields = ('template__name', 'subject__name')