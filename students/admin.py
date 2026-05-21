from django.contrib import admin, messages
from import_export.admin import ImportExportModelAdmin
from .models import Student, AgeGroup
from .resources import StudentResource
from .utils import auto_assign_hall


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
    actions           = (
        'mark_as_pending_and_clear_hall',
        'auto_reassign_selected',
        'reset_and_auto_reassign_selected',
    )

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
            'fields': (
                'parent', 'hall', 'status',
                'uses_bus', 'bus_notes', 'notes'
            )
        }),
    )

    @admin.action(description='إرجاع الطلاب المحددين إلى: في انتظار التسكين + حذف القاعة')
    def mark_as_pending_and_clear_hall(self, request, queryset):
        updated = queryset.update(
            status=Student.STATUS_PENDING,
            hall=None
        )
        self.message_user(
            request,
            f'✅ تم تحويل {updated} طالب إلى "في انتظار التسكين" مع إزالة القاعة الحالية.',
            level=messages.SUCCESS
        )

    @admin.action(description='إعادة التسكين التلقائي للطلاب المحددين')
    def auto_reassign_selected(self, request, queryset):
        success_count = 0
        failed_count  = 0

        for student in queryset:
            hall, msg = auto_assign_hall(student)
            if hall:
                success_count += 1
            else:
                failed_count += 1

        if success_count and not failed_count:
            level = messages.SUCCESS
        elif success_count and failed_count:
            level = messages.WARNING
        else:
            level = messages.ERROR

        self.message_user(
            request,
            f'تمت إعادة التسكين التلقائي لـ {success_count} طالب، وتعذر تسكين {failed_count} طالب.',
            level=level
        )

    @admin.action(description='تفريغ القاعات ثم إعادة التسكين التلقائي للمحددين')
    def reset_and_auto_reassign_selected(self, request, queryset):
        success_count = 0
        failed_count  = 0

        for student in queryset:
            student.hall   = None
            student.status = Student.STATUS_PENDING
            student.save(update_fields=['hall', 'status'])

            hall, msg = auto_assign_hall(student)
            if hall:
                success_count += 1
            else:
                failed_count += 1

        if success_count and not failed_count:
            level = messages.SUCCESS
        elif success_count and failed_count:
            level = messages.WARNING
        else:
            level = messages.ERROR

        self.message_user(
            request,
            f'✅ تمت إعادة ضبط وإعادة تسكين {success_count} طالب، ولم يتم تسكين {failed_count} طالب.',
            level=level
        )