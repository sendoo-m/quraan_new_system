from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, SiteSettings, GeneralSupervisorHallAssignment


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = (
        'username', 'first_name', 'last_name', 'role', 'phone', 'is_active'
    )
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'phone')

    fieldsets = UserAdmin.fieldsets + (
        ('بيانات إضافية', {
            'fields': ('role', 'phone', 'profile_picture')
        }),
        ('صلاحيات النظام', {
            'fields': (
                'can_manage_users',
                'can_manage_halls',
                'can_manage_students',
                'can_manage_attendance',
                'can_manage_evaluations',
                'can_manage_settings',
            )
        }),
    )


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone', 'allow_registration', 'auto_assign_halls', 'updated_at')
    readonly_fields = ('updated_at',)
    fieldsets = (
        ('بيانات المقرأة', {
            'fields': ('name', 'logo', 'address', 'phone', 'email', 'description')
        }),
        ('إعدادات التسجيل', {
            'fields': ('allow_registration', 'auto_assign_halls', 'min_age_limit', 'max_age_limit')
        }),
        ('إعدادات الحضور', {
            'fields': ('attendance_start_time', 'late_threshold_minutes')
        }),
        ('التواصل', {
            'fields': ('facebook', 'whatsapp')
        }),
        ('التتبع', {
            'fields': ('updated_at', 'updated_by')
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(GeneralSupervisorHallAssignment)
class GeneralSupervisorHallAssignmentAdmin(admin.ModelAdmin):
    list_display = ('supervisor', 'hall', 'assigned_at')
    list_filter = ('supervisor', 'hall')
    search_fields = ('supervisor__username', 'supervisor__first_name', 'hall__name')

# from django.contrib import admin
# from django.contrib.auth.admin import UserAdmin
# from .models import User


# @admin.register(User)
# class CustomUserAdmin(UserAdmin):
#     list_display = ('username', 'get_full_name', 'role', 'phone', 'is_active')
#     list_filter = ('role', 'is_active')
#     search_fields = ('username', 'first_name', 'last_name', 'phone')

#     fieldsets = UserAdmin.fieldsets + (
#         ('بيانات إضافية', {
#             'fields': ('role', 'phone', 'profile_picture')
#         }),
#     )
