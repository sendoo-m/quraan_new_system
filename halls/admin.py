from django.contrib import admin
from .models import Hall, Subject, HallSchedule


@admin.register(Hall)
class HallAdmin(admin.ModelAdmin):
    list_display  = (
        'name', 'age_group', 'teacher',
        'supervisor', 'get_current_students_count',
        'max_students', 'is_active'
    )
    list_filter   = ('age_group', 'is_active')
    search_fields = ('name', 'location')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_active')


@admin.register(HallSchedule)
class HallScheduleAdmin(admin.ModelAdmin):
    list_display = ('hall', 'subject', 'day', 'start_time', 'end_time')
    list_filter  = ('hall', 'day')
    search_fields = ('hall__name', 'subject__name')
    