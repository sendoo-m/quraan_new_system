from django.contrib import admin
from .models import StudentAttendance, StaffAttendance


@admin.register(StudentAttendance)
class StudentAttendanceAdmin(admin.ModelAdmin):
    list_display  = ('student', 'hall', 'date', 'status', 'arrival_time', 'recorded_by')
    list_filter   = ('status', 'date', 'hall')
    search_fields = ('student__first_name', 'student__last_name')
    date_hierarchy = 'date'


@admin.register(StaffAttendance)
class StaffAttendanceAdmin(admin.ModelAdmin):
    list_display  = ('staff', 'date', 'status', 'check_in', 'check_out', 'recorded_by')
    list_filter   = ('status', 'date', 'staff__role')
    search_fields = ('staff__first_name', 'staff__last_name')
    date_hierarchy = 'date'
