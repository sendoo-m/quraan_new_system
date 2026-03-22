from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'get_full_name', 'role', 'phone', 'is_active')
    list_filter = ('role', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'phone')

    fieldsets = UserAdmin.fieldsets + (
        ('بيانات إضافية', {
            'fields': ('role', 'phone', 'profile_picture')
        }),
    )
