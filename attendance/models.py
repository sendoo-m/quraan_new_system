from django.db import models
from django.utils import timezone
from accounts.models import User
from students.models import Student
from halls.models import Hall


class StudentAttendance(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_LATE = 'late'
    STATUS_EXCUSED = 'excused'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'حاضر'),
        (STATUS_ABSENT, 'غائب'),
        (STATUS_LATE, 'متأخر'),
        (STATUS_EXCUSED, 'غياب بعذر'),
    ]

    student = models.ForeignKey(
        Student,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='الطالب'
    )
    hall = models.ForeignKey(
        Hall,
        on_delete=models.CASCADE,
        related_name='attendances',
        verbose_name='القاعة'
    )
    date = models.DateField(default=timezone.now, verbose_name='التاريخ')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PRESENT,
        verbose_name='الحالة'
    )
    arrival_time = models.TimeField(null=True, blank=True, verbose_name='وقت الحضور')
    notes = models.CharField(max_length=200, blank=True, verbose_name='ملاحظات')
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='student_attendances_recorded',
        limit_choices_to={'role__in': ['hall_supervisor', 'general_supervisor', 'general_manager']},
        verbose_name='سجّله'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.get_full_name()} | {self.date} | {self.get_status_display()}"

    class Meta:
        verbose_name = 'حضور طالب'
        verbose_name_plural = 'حضور الطلاب'
        ordering = ['-date', 'hall']
        constraints = [
            models.UniqueConstraint(
                fields=['student', 'date'],
                name='unique_student_attendance_per_day'
            )
        ]


class StaffAttendance(models.Model):
    STATUS_PRESENT = 'present'
    STATUS_ABSENT = 'absent'
    STATUS_LATE = 'late'
    STATUS_EXCUSED = 'excused'

    STATUS_CHOICES = [
        (STATUS_PRESENT, 'حاضر'),
        (STATUS_ABSENT, 'غائب'),
        (STATUS_LATE, 'متأخر'),
        (STATUS_EXCUSED, 'غياب بعذر'),
    ]

    staff = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='staff_attendances',
        limit_choices_to={'role__in': ['teacher', 'hall_supervisor']},
        verbose_name='الموظف'
    )
    date = models.DateField(default=timezone.now, verbose_name='التاريخ')
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default=STATUS_PRESENT,
        verbose_name='الحالة'
    )
    check_in = models.TimeField(null=True, blank=True, verbose_name='وقت الحضور')
    check_out = models.TimeField(null=True, blank=True, verbose_name='وقت الانصراف')
    notes = models.CharField(max_length=200, blank=True, verbose_name='ملاحظات')
    recorded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='staff_attendances_recorded',
        limit_choices_to={'role__in': ['general_supervisor', 'general_manager']},
        verbose_name='سجّله'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.staff.get_full_name()} | {self.date} | {self.get_status_display()}"

    class Meta:
        verbose_name = 'حضور موظف'
        verbose_name_plural = 'حضور الموظفين'
        ordering = ['-date', 'staff']
        constraints = [
            models.UniqueConstraint(
                fields=['staff', 'date'],
                name='unique_staff_attendance_per_day'
            )
        ]